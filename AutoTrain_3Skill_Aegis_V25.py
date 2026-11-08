# Auto Train 3Skill - Chien Quoc 2D Aegis V25
# Repeats keyboard shortcuts only; no monster/loot recognition.
import ctypes
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

user32 = ctypes.windll.user32
KEYS = {str(i): 0x30 + i for i in range(10)}
KEYS.update({chr(65+i): 65+i for i in range(26)})
KEYS.update({f'F{i}': 0x70+i-1 for i in range(1, 13)})
KEYS.update({'TAB': 0x09, 'SPACE': 0x20})
KEYEVENTF_KEYUP = 0x0002

class AutoTrain:
    def __init__(self, root):
        self.root = root
        root.title('Auto Train 3Skill - Chien Quoc 2D Aegis V25')
        root.geometry('540x490')
        root.resizable(False, False)
        self.running = False
        self.closing = False
        self.hotkey_down = False
        self.target = tk.StringVar(value='Chien Quoc 2D')
        self.keys = [tk.StringVar(value=k) for k in ('1', '2', '3')]
        self.delays = [tk.StringVar(value=d) for d in ('600', '800', '1000')]
        self.tab_enabled = tk.BooleanVar(value=True)
        self.space_enabled = tk.BooleanVar(value=True)
        self.tab_delay = tk.StringVar(value='3000')
        self.space_delay = tk.StringVar(value='5000')
        self.status = tk.StringVar(value='Da dung - F8 de bat/tat')
        ttk.Label(root, text='AUTO TRAIN 3SKILL - AEGIS V25', font=('Segoe UI', 15, 'bold')).pack(pady=12)
        top = ttk.Frame(root)
        top.pack(fill='x', padx=25)
        ttk.Label(top, text='Ten cua so game chua:').pack(side='left')
        ttk.Entry(top, textvariable=self.target, width=30).pack(side='right')
        table = ttk.Frame(root)
        table.pack(pady=12)
        for j, title in enumerate(('Ky nang', 'Phim', 'Khoang lap (ms)')):
            ttk.Label(table, text=title).grid(row=0, column=j, padx=13)
        for i in range(3):
            ttk.Label(table, text=f'Skill {i+1}').grid(row=i+1, column=0, pady=6)
            ttk.Combobox(table, textvariable=self.keys[i], values=list(KEYS), state='readonly', width=9).grid(row=i+1, column=1)
            ttk.Entry(table, textvariable=self.delays[i], width=14).grid(row=i+1, column=2)
        extra = ttk.LabelFrame(root, text='Tu chon quai va nhat do (lap phim theo chu ky)')
        extra.pack(fill='x', padx=24, pady=7)
        ttk.Checkbutton(extra, text='Tab - Chon quai', variable=self.tab_enabled).grid(row=0, column=0, sticky='w', padx=10, pady=8)
        ttk.Entry(extra, textvariable=self.tab_delay, width=9).grid(row=0, column=1)
        ttk.Label(extra, text='ms').grid(row=0, column=2, padx=5)
        ttk.Checkbutton(extra, text='Space - Nhat do', variable=self.space_enabled).grid(row=1, column=0, sticky='w', padx=10, pady=8)
        ttk.Entry(extra, textvariable=self.space_delay, width=9).grid(row=1, column=1)
        ttk.Label(extra, text='ms').grid(row=1, column=2, padx=5)
        controls = ttk.Frame(root)
        controls.pack(pady=9)
        ttk.Button(controls, text='Bat dau (F8)', command=self.start).pack(side='left', padx=8)
        ttk.Button(controls, text='Dung (F8)', command=self.stop).pack(side='left', padx=8)
        ttk.Label(root, textvariable=self.status).pack(pady=5)
        ttk.Label(root, text='Chi gui phim khi cua so game duoc chon. F8 bat/tat toan cuc.', foreground='#666').pack()
        ttk.Label(root, text='Khong nhan biet quai chet hay do roi; can thu trong game.', foreground='#666').pack(pady=5)
        root.protocol('WM_DELETE_WINDOW', self.close)
        threading.Thread(target=self.hotkey_loop, daemon=True).start()

    def foreground_is_game(self, needle):
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, len(buf))
        return needle.casefold() in buf.value.casefold()

    def send_key(self, vk):
        user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.035)
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

    def start(self):
        if self.running or self.closing:
            return
        try:
            raw = [int(v.get()) for v in self.delays]
            if self.tab_enabled.get():
                raw.append(int(self.tab_delay.get()))
            if self.space_enabled.get():
                raw.append(int(self.space_delay.get()))
            if any(not 50 <= x <= 60000 for x in raw):
                raise ValueError()
            keys = [KEYS[k.get().upper()] for k in self.keys]
            intervals = [int(v.get()) / 1000 for v in self.delays]
            if self.tab_enabled.get():
                keys.append(KEYS['TAB'])
                intervals.append(int(self.tab_delay.get()) / 1000)
            if self.space_enabled.get():
                keys.append(KEYS['SPACE'])
                intervals.append(int(self.space_delay.get()) / 1000)
            needle = self.target.get().strip()
            if not needle:
                messagebox.showerror('Thieu ten cua so', 'Hay nhap mot phan ten cua so game.')
                return
        except (ValueError, KeyError):
            messagebox.showerror('Cau hinh khong hop le', 'Khoang lap phai tu 50 den 60000 ms.')
            return
        self.running = True
        self.status.set('Dang chay - chuyen sang cua so game')
        threading.Thread(target=self.worker, args=(keys, intervals, needle), daemon=True).start()

    def stop(self):
        self.running = False
        self.status.set('Da dung - F8 de bat/tat')

    def worker(self, keys, intervals, needle):
        due = [time.monotonic()] * len(keys)
        while self.running and not self.closing:
            if not self.foreground_is_game(needle):
                due = [time.monotonic()] * len(keys)
                time.sleep(0.1)
                continue
            for i, vk in enumerate(keys):
                if not self.running or not self.foreground_is_game(needle):
                    break
                if time.monotonic() >= due[i]:
                    self.send_key(vk)
                    due[i] = time.monotonic() + intervals[i]
            time.sleep(0.015)

    def hotkey_loop(self):
        while not self.closing:
            down = bool(user32.GetAsyncKeyState(0x77) & 0x8000)
            if down and not self.hotkey_down:
                try:
                    self.root.after(0, self.stop if self.running else self.start)
                except RuntimeError:
                    break
            self.hotkey_down = down
            time.sleep(0.08)

    def close(self):
        self.closing = True
        self.running = False
        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    AutoTrain(root)
    root.mainloop()
