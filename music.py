import math
import threading
import wave
import struct
import io

# ---------- Music system ----------
_music_enabled   = False
_music_stop_evt  = threading.Event()
_music_thread    = None
_music_audio_cache = None   # generated once, reused

def _get_f(m): return 440 * (2 ** ((m - 69) / 12))

def _generate_music_bytes():
    global _music_audio_cache
    if _music_audio_cache is not None:
        return _music_audio_cache
    RATE = 44100; BPM = 70; BEAT = 60 / BPM; AMP = 7500
    score = [
        ([43,55,71],3.0),([74],1.0),([43,55,76],4.0),
        ([42,54,69],3.0),([73],1.0),([42,54,74],4.0),
        ([43,55,81],2.0),([83],2.0),([42,54,78],4.0),
        ([40,52,74],2.0),([76],2.0),([38,50,78],4.0),
        ([43,55,78],2.0),([81],2.0),([42,54,76],4.0),
        ([40,52,74],2.0),([71],2.0),([38,50,69],2.0),([66],2.0),
        ([43,55,74],1.0),([76],1.0),([78],1.0),([81],1.0),
        ([42,54,78],2.0),([76],2.0),([43,55,71,74],8.0),
    ]
    buf_io = io.BytesIO()
    with wave.open(buf_io, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(RATE)
        frames = []
        for notes, beats in score:
            n = int(RATE * beats * BEAT)
            buf = [0.0] * n
            for idx, m in enumerate(notes):
                freq = _get_f(m)
                off  = int(idx * 0.03 * RATE)
                for i in range(off, n):
                    t   = (i - off) / RATE
                    env = math.exp(-1.5 * (i - off) / (n - off))
                    if t < 0.05: env *= t / 0.05
                    buf[i] += (math.sin(2*math.pi*freq*t) + 0.15*math.sin(4*math.pi*freq*t)) * env
            for v in buf:
                c = max(-1.0, min(1.0, v / (len(notes) * 1.2)))
                frames.append(struct.pack('<h', int(c * AMP)))
        wf.writeframes(b''.join(frames))
    _music_audio_cache = buf_io.getvalue()
    return _music_audio_cache

def _music_worker():
    try:
        import winsound
        data = _generate_music_bytes()
        while not _music_stop_evt.is_set():
            winsound.PlaySound(data, winsound.SND_MEMORY | winsound.SND_NODEFAULT)
    except Exception:
        pass

def music_start():
    global _music_thread
    if not _music_enabled:
        return
    if _music_thread and _music_thread.is_alive():
        return
    _music_stop_evt.clear()
    _music_thread = threading.Thread(target=_music_worker, daemon=True)
    _music_thread.start()

def music_stop():
    _music_stop_evt.set()
    try:
        import winsound
        winsound.PlaySound(None, winsound.SND_PURGE)
    except Exception:
        pass

