"""
Змінювач голосу: Python (вікно + звук) + C++ (обробка звуку)

1. pip install -r requirements.txt
2. Збери C++ частину: g++ -O2 -shared -static-libgcc -static-libstdc++ -o voice_dsp.dll effects.cpp
3. python voice_changer.py

Готовий .exe: запусти build.bat або дивись README.md

Щоб Discord/гра чули змінений голос: встанови VB-Cable,
тут у «Вихід» обери CABLE Input, а в Discord мікрофон CABLE Output.
"""

import ctypes
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024

EFFECTS = [
    "Без ефекту",
    "Свій тон (слайдер)",
    "Білка",
    "Демон",
    "Робот",
    "Луна",
]

# ---------- Завантаження C++ бібліотеки ----------
# Для зібраного .exe (PyInstaller) файли лежать у тимчасовій папці _MEIPASS
here = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
lib_name = "voice_dsp.dll" if sys.platform == "win32" else "voice_dsp.so"
lib_path = os.path.join(here, lib_name)

try:
    lib = ctypes.CDLL(lib_path)
except OSError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Немає C++ бібліотеки",
        f"Не знайдено {lib_name}.\nСпочатку запусти build.bat.")
    sys.exit(1)

FP = ctypes.POINTER(ctypes.c_float)
lib.vc_process.argtypes = [FP, FP, ctypes.c_int, ctypes.c_int, ctypes.c_float]
lib.vc_process.restype = None
lib.vc_reset.argtypes = []
lib.vc_reset.restype = None


class Engine:
    def __init__(self):
        self.stream = None
        self.effect = 0
        self.semitones = 0.0
        self.volume = 1.0

    def callback(self, indata, outdata, frames, time_info, status):
        x = np.ascontiguousarray(indata[:, 0], dtype=np.float32)
        y = np.empty_like(x)
        lib.vc_process(x.ctypes.data_as(FP), y.ctypes.data_as(FP),
                       frames, self.effect, self.semitones)
        outdata[:, 0] = np.clip(y * self.volume, -1.0, 1.0)

    def start(self, in_dev, out_dev):
        lib.vc_reset()
        self.stream = sd.Stream(
            samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE,
            device=(in_dev, out_dev), channels=1, dtype="float32",
            callback=self.callback)
        self.stream.start()

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None


engine = Engine()

# ---------- Просте біле вікно ----------
BG = "white"
root = tk.Tk()
root.title("Змінювач голосу")
root.configure(bg=BG)
try:
    root.iconbitmap(os.path.join(here, "icon.ico"))
except Exception:
    pass
root.geometry("380x420")
root.resizable(False, False)

style = ttk.Style()
style.configure("TCombobox", fieldbackground="white", background="white")


def label(text):
    return tk.Label(root, text=text, bg=BG, fg="black", anchor="w")


# Пристрої
hostapis = sd.query_hostapis()
in_list, out_list = [], []
for i, d in enumerate(sd.query_devices()):
    name = f"{d['name']} [{hostapis[d['hostapi']]['name']}]"
    if d["max_input_channels"] > 0:
        in_list.append((name, i))
    if d["max_output_channels"] > 0:
        out_list.append((name, i))


def pick_default(items, default_index):
    for pos, (_, idx) in enumerate(items):
        if idx == default_index:
            return pos
    return 0


label("Мікрофон:").pack(fill="x", padx=15, pady=(15, 2))
in_box = ttk.Combobox(root, values=[n for n, _ in in_list], state="readonly")
in_box.current(pick_default(in_list, sd.default.device[0]))
in_box.pack(fill="x", padx=15)

label("Вихід (для Discord: CABLE Input):").pack(fill="x", padx=15, pady=(10, 2))
out_box = ttk.Combobox(root, values=[n for n, _ in out_list], state="readonly")
out_box.current(pick_default(out_list, sd.default.device[1]))
out_box.pack(fill="x", padx=15)

label("Ефект:").pack(fill="x", padx=15, pady=(10, 2))
effect_box = ttk.Combobox(root, values=EFFECTS, state="readonly")
effect_box.current(0)
effect_box.pack(fill="x", padx=15)


def on_effect(_=None):
    engine.effect = effect_box.current()
    lib.vc_reset()


effect_box.bind("<<ComboboxSelected>>", on_effect)

label("Тон (півтони):").pack(fill="x", padx=15, pady=(10, 0))
pitch = tk.Scale(root, from_=-12, to=12, orient="horizontal", bg=BG,
                 highlightthickness=0, troughcolor="#e6e6e6",
                 command=lambda v: setattr(engine, "semitones", float(v)))
pitch.pack(fill="x", padx=15)

label("Гучність (%):").pack(fill="x", padx=15, pady=(5, 0))
vol = tk.Scale(root, from_=0, to=200, orient="horizontal", bg=BG,
               highlightthickness=0, troughcolor="#e6e6e6",
               command=lambda v: setattr(engine, "volume", float(v) / 100))
vol.set(100)
vol.pack(fill="x", padx=15)

status = tk.Label(root, text="Зупинено", bg=BG, fg="gray")
btn = tk.Button(root, text="Запустити", bg="#f0f0f0", relief="groove", height=2)


def toggle():
    if engine.stream:
        engine.stop()
        btn.config(text="Запустити")
        status.config(text="Зупинено")
        in_box.config(state="readonly")
        out_box.config(state="readonly")
        return
    try:
        engine.start(in_list[in_box.current()][1], out_list[out_box.current()][1])
    except Exception as e:
        messagebox.showerror(
            "Помилка",
            f"Не вдалося запустити звук:\n{e}\n\n"
            "Спробуй обрати пристрої одного типу (наприклад, обидва MME).")
        return
    btn.config(text="Зупинити")
    status.config(text="Працює")
    in_box.config(state="disabled")
    out_box.config(state="disabled")


btn.config(command=toggle)
btn.pack(fill="x", padx=15, pady=(15, 5))
status.pack()


def on_close():
    engine.stop()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
