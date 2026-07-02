import sys
import ctypes
import threading
from ctypes import CFUNCTYPE, POINTER, Structure, c_int, c_void_p, windll
from ctypes.wintypes import DWORD, MSG, ULONG

# Windows hook event constants
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 256

class KBDLLHOOKSTRUCT(Structure):
    _fields_ = [
        ("vkCode", DWORD),
        ("scanCode", DWORD),
        ("flags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", c_void_p),
    ]

# Raw storage for the recorded tokens
pressed_tokens = []
hook_id = None
msg_loop_thread_id = DWORD(0)

def hook_procedure(nCode, wParam, lParam):
    if nCode >= 0 and wParam == WM_KEYDOWN:
        kbd_ptr = ctypes.cast(lParam, POINTER(KBDLLHOOKSTRUCT))
        kbd = kbd_ptr.contents
        vk_code = kbd.vkCode

        # Explicitly track structural layout keys in the token list
        if vk_code == 13:          # Enter key
            pressed_tokens.append("(ent)")
            return windll.user32.CallNextHookEx(None, nCode, wParam, lParam)
        elif vk_code == 8:         # Backspace/Delete key
            pressed_tokens.append("(del)")
            return windll.user32.CallNextHookEx(None, nCode, wParam, lParam)
        elif vk_code == 32:        # Space bar
            pressed_tokens.append(" ")
            return windll.user32.CallNextHookEx(None, nCode, wParam, lParam)

        # Translate hardware signals into text characters safely
        state = (c_int * 256)()
        windll.user32.GetKeyboardState(state)
        buff = (c_int * 2)()
        result = windll.user32.ToUnicode(vk_code, kbd.scanCode, state, buff, 2, 0)

        if result > 0:
            char = chr(buff[0])
            # Skip recording the literal trigger '¬' in background memory 
            if char != "¬" and vk_code >= 32:
                pressed_tokens.append(char)

    return windll.user32.CallNextHookEx(None, nCode, wParam, lParam)

def start_keyboard_hook():
    global hook_id, msg_loop_thread_id
    
    msg_loop_thread_id = windll.kernel32.GetCurrentThreadId()
    
    CALLBACK_FUNC = CFUNCTYPE(c_void_p, c_int, c_void_p, c_void_p)
    pointer_to_procedure = CALLBACK_FUNC(hook_procedure)

    windll.user32.SetWindowsHookExA.argtypes = [c_int, CALLBACK_FUNC, c_void_p, DWORD]
    windll.user32.SetWindowsHookExA.restype = c_void_p
    windll.user32.CallNextHookEx.argtypes = [c_void_p, c_int, c_void_p, c_void_p]
    windll.user32.CallNextHookEx.restype = c_void_p

    hook_id = windll.user32.SetWindowsHookExA(WH_KEYBOARD_LL, pointer_to_procedure, None, 0)

    msg = MSG()
    while windll.user32.GetMessageA(POINTER(MSG)(msg), None, 0, 0) != 0:
        windll.user32.TranslateMessage(POINTER(MSG)(msg))
        windll.user32.DispatchMessageA(POINTER(MSG)(msg))

def collapse_tokens(tokens):
    """Collapses consecutive (del) and (ent) markers into shorthand multipliers."""
    if not tokens:
        return ""
        
    result = []
    i = 0
    n = len(tokens)
    
    while i < n:
        current = tokens[i]
        
        # If it is a repeatable target tag, count how many follow it consecutively
        if current in ("(del)", "(ent)"):
            count = 0
            while i < n and tokens[i] == current:
                count += 1
                i += 1
            result.append(f"{current}x{count}")
        else:
            result.append(current)
            i += 1
            
    return "".join(result)

# 1. Spin up the background keylogger on its own separate thread
listener_thread = threading.Thread(target=start_keyboard_hook, daemon=True)
listener_thread.start()

# 2. Keep the main terminal loop waiting for your terminal input command
while True:
    user_command = input()
    if user_command.strip() == "¬":
        break

# 3. Clean up and shut down background tasks upon receiving the exit command
if hook_id:
    windll.user32.UnhookWindowsHookEx.argtypes = [c_void_p]
    windll.user32.UnhookWindowsHookEx(hook_id)
    windll.user32.PostThreadMessageA(msg_loop_thread_id, 18, 0, 0) # 18 = WM_QUIT

# 4. Collapse the repetitions and output the final log
final_output = collapse_tokens(pressed_tokens)

print("\n=== YOUR BLIND TYPED TEXT ===")
print(final_output)
print("=============================")
sys.stdout.flush()
