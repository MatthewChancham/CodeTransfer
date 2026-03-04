import tkinter as tk
import time
import threading
import random

WORDS = [
    "hello", "world", "python", "banana", "cloud",
    "window", "coffee", "magic", "random", "infinite"
]

def spawn_window():
    win = tk.Tk()
    win.title("Random Word")
    word = random.choice(WORDS)
    label = tk.Label(win, text=word, font=("Arial", 1000))
    label.pack(padx=2500, pady=1500)
    label = tk.Label(win, text=word, font=("Arial", 1000))
    label.pack(padx=2500, pady=1500)
    label = tk.Label(win, text=word, font=("Arial", 1000))
    label.pack(padx=2500, pady=1500)
    label = tk.Label(win, text=word, font=("Arial", 1000))
    label.pack(padx=2500, pady=1500)
    label = tk.Label(win, text=word, font=("Arial", 1000))
    label.pack(padx=2500, pady=1500)
    label = tk.Label(win, text=word, font=("Arial", 1000))
    label.pack(padx=2500, pady=1500)
    label = tk.Label(win, text=word, font=("Arial", 1000))
    label.pack(padx=2500, pady=1500)
    label = tk.Label(win, text=word, font=("Arial", 1000))
    label.pack(padx=2500, pady=1500)
    label = tk.Label(win, text=word, font=("Arial", 1000))
    label.pack(padx=2500, pady=1500)
    label = tk.Label(win, text=word, font=("Arial", 1000))
    label.pack(padx=2500, pady=1500)
    label = tk.Label(win, text=word, font=("Arial", 1000))
    label.pack(padx=2500, pady=1500)
    label = tk.Label(win, text=word, font=("Arial", 1000))
    label.pack(padx=2500, pady=1500)
    label = tk.Label(win, text=word, font=("Arial", 1000))
    label.pack(padx=2500, pady=1500)
    label = tk.Label(win, text=word, font=("Arial", 1000))
    label.pack(padx=2500, pady=1500)
    label = tk.Label(win, text=word, font=("Arial", 1000))
    label.pack(padx=2500, pady=1500)
    win.mainloop()

def loop_windows():
    while True:
        threading.Thread(target=spawn_window).start()
loop_windows()
