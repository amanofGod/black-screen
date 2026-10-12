import ctypes as C
from ctypes import wintypes as W
import sys
import time
import tkinter as tk
from tkinter import ttk

u = C.WinDLL('user32', use_last_error=True)

def api(name, args, result):
    fn = getattr(u, name)
    fn.argtypes, fn.restype = args, result
    return fn

EnumProc = C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
api('EnumWindows', [EnumProc, W.LPARAM], W.BOOL)
api('GetWindowTextW', [W.HWND, W.LPWSTR, C.c_int], C.c_int)
api('GetWindowThreadProcessId', [W.HWND, C.POINTER(W.DWORD)], W.DWORD)
api('GetClientRect', [W.HWND, C.POINTER(W.RECT)], W.BOOL)
api('IsWindow', [W.HWND], W.BOOL)
api('IsIconic', [W.HWND], W.BOOL)
api('PostMessageW', [W.HWND, W.UINT, W.WPARAM, W.LPARAM], W.BOOL)
api('GetForegroundWindow', [], W.HWND)
api('GetCursorPos', [C.POINTER(W.POINT)], W.BOOL)
api('GetAsyncKeyState', [C.c_int], C.c_short)

class Pad(C.Structure):
    _fields_ = [('buttons', W.WORD), ('lt', W.BYTE), ('rt', W.BYTE),
                ('lx', C.c_short), ('ly', C.c_short), ('rx', C.c_short), ('ry', C.c_short)]
class State(C.Structure):
    _fields_ = [('packet', W.DWORD), ('pad', Pad)]

xi = C.WinDLL('xinput1_4')
xi.XInputGetState.argtypes = [W.DWORD, C.POINTER(State)]
xi.XInputGetState.restype = W.DWORD

def pads():
    result = {}
    for index in range(4):
        state = State()
        if xi.XInputGetState(index, C.byref(state)) == 0:
            result[index] = state.pad.rt
    return result

def title(hwnd):
    buf = C.create_unicode_buffer(512)
    u.GetWindowTextW(hwnd, buf, len(buf))
    return buf.value

def pid(hwnd):
    value = W.DWORD()
    u.GetWindowThreadProcessId(hwnd, C.byref(value))
    return value.value

def size(hwnd):
    rect = W.RECT()
    if not u.GetClientRect(hwnd, C.byref(rect)):
        raise RuntimeError('无法读取窗口尺寸')
    return rect.right, rect.bottom

def games():
    result = []
    @EnumProc
    def visit(hwnd, _):
        if '洛克王国' in title(hwnd) and '世界' in title(hwnd):
            result.append(hwnd)
        return True
    u.EnumWindows(visit, 0)
    return result

class Target:
    def __init__(self, hwnd):
        if not hwnd or not u.IsWindow(hwnd):
            raise RuntimeError('目标窗口不存在')
        self.hwnd, self.pid, self.title = hwnd, pid(hwnd), title(hwnd)
        self.size = size(hwnd)

    def validate(self):
        if not u.IsWindow(self.hwnd) or pid(self.hwnd) != self.pid or title(self.hwnd) != self.title:
            raise RuntimeError('游戏窗口已关闭或发生变化，请重新绑定')
        if u.IsIconic(self.hwnd):
            raise RuntimeError('游戏已最小化，请保持窗口打开')
        if size(self.hwnd) != self.size or min(self.size) <= 0:
            raise RuntimeError('窗口尺寸改变，请重新绑定')

    def click(self, require_foreground=None):
        self.validate()
        foreground_before = u.GetForegroundWindow() == self.hwnd
        if require_foreground is not None and foreground_before != require_foreground:
            expected = '前台' if require_foreground else '后台'
            raise RuntimeError(f'已取消：游戏不在{expected}，未发送点击')
        x, y = (n // 2 for n in self.size)
        point = (x & 0xffff) | ((y & 0xffff) << 16)
        if not u.PostMessageW(self.hwnd, 0x201, 1, point):
            raise C.WinError(C.get_last_error())
        try:
            time.sleep(0.06)
        finally:
            if u.IsWindow(self.hwnd) and pid(self.hwnd) == self.pid:
                if not u.PostMessageW(self.hwnd, 0x202, 0, point):
                    raise C.WinError(C.get_last_error())
        return foreground_before, u.GetForegroundWindow() == self.hwnd

class App:
    def __init__(self, root):
        self.root, self.target = root, None
        self.armed, self.deadline, self.due = False, 0, None
        self.previous, self.count = {}, 0
        self.test_mode = None
        root.title('洛克左键前后台对照测试 v2（默认停止）')
        root.geometry('700x590')
        root.protocol('WM_DELETE_WINDOW', self.close)
        frame = ttk.Frame(root, padding=18)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='左键前后台对照测试 v2', font=('Microsoft YaHei UI', 16)).pack(anchor='w')
        instructions = ('1. 游戏停在可测试的场景，避开购买、删除等按钮。\n'
            '2. 绑定游戏，点“前台测试”，8 秒内切回游戏并保持。\n'
            '3. 不按鼠标或 RT，观察倒计时结束时游戏是否动作。\n'
            '后台测试则切到工作窗口；两种测试使用相同点击方式。\n'
            '每次按下 RT 发一次左键；60 秒后自动停止。\n'
            'Ctrl + Alt + F10 可随时停止。不会移动鼠标或切换焦点。')
        ttk.Label(frame, text=instructions, justify='left').pack(anchor='w', pady=12)
        self.target_text = tk.StringVar(value='未绑定')
        self.pad_text = tk.StringVar()
        self.status = tk.StringVar(value='已停止；尚未向游戏发送点击')
        self.last_result = tk.StringVar(value='上次结果：尚未测试')
        for var in (self.target_text, self.pad_text, self.status, self.last_result):
            ttk.Label(frame, textvariable=var, wraplength=600).pack(anchor='w', pady=5)
        row = ttk.Frame(frame)
        row.pack(anchor='w', pady=12)
        for label, cmd in [('绑定游戏', self.bind), ('启用 RT 转发（60 秒）', self.arm),
                           ('停止', self.stop)]:
            ttk.Button(row, text=label, command=cmd).pack(side='left', padx=3)
        tests = ttk.Frame(frame)
        tests.pack(anchor='w', pady=5)
        ttk.Button(tests, text='前台测试（8 秒后一次）', command=lambda: self.schedule(True)).pack(side='left', padx=3)
        ttk.Button(tests, text='后台测试（8 秒后一次）', command=lambda: self.schedule(False)).pack(side='left', padx=3)
        ttk.Label(frame, wraplength=595, text=(
            '“已投递”仅表示 Windows 接收消息，不证明游戏响应。\n'
            '消息使用游戏画面中心坐标，桌面光标保持不变。\n'
            '测试 RT 转发时，先暂停其他软件的 RT→鼠标/Tab 映射，避免它点击工作窗口。\n'
            '权限拒绝或无反应时请反馈结果；工具不会自动提权或修改游戏。')).pack(anchor='w', pady=8)
        root.after(100, self.poll)

    def bind(self):
        self.stop()
        self.target = None
        self.target_text.set('未绑定')
        found = games()
        if len(found) != 1:
            self.status.set('未找到唯一游戏窗口，请只打开一个游戏客户端')
            return
        try:
            self.target = Target(found[0])
            self.target_text.set(f'已绑定：{self.target.title} ｜ 进程 {self.target.pid}')
        except Exception as exc:
            self.target = None
            self.status.set(str(exc))

    def ready(self):
        if self.target is None:
            self.status.set('请先绑定游戏')
            return False
        try:
            self.target.validate()
            return True
        except Exception as exc:
            self.status.set(str(exc))
            return False

    def arm(self):
        self.stop()
        if not self.ready():
            return
        self.previous = pads()
        if not self.previous:
            self.status.set('没有检测到 XInput 手柄，可用前台/后台倒计时测试')
            return
        self.armed, self.deadline = True, time.monotonic() + 60
        self.status.set('已启用 RT 转发；请切到工作窗口，再松开并按下 RT')

    def schedule(self, foreground=False):
        self.stop()
        if self.ready():
            self.test_mode = foreground
            self.due = time.monotonic() + 8
            self.countdown_status()

    def countdown_status(self):
        remaining = max(0, int(self.due - time.monotonic()) + 1)
        action = '切回游戏并保持前台' if self.test_mode else '切到工作窗口，让游戏留在后台'
        self.status.set(f'{remaining} 秒后发送一次左键，请{action}')

    def stop(self):
        self.armed, self.due = False, None
        self.status.set(f'已停止；累计投递 {self.count} 次（游戏响应待观察）')

    def send(self, require_foreground=None):
        try:
            before, after = self.target.click(require_foreground)
            self.count += 1
            self.status.set(f'已投递 {self.count} 次；请观察游戏是否响应')
            mode = 'RT 转发' if require_foreground is None else ('前台测试' if require_foreground else '后台测试')
            focus = lambda value: '游戏在前台' if value else '游戏在后台'
            note = '；期间焦点变化，本次不能用于对照' if before != after else ''
            self.last_result.set(f'上次结果：{mode}已投递；发送前：{focus(before)}；发送后：{focus(after)}{note}。游戏动作需人工观察。')
        except Exception as exc:
            self.stop()
            self.status.set(f'已停止：{exc}')
            self.last_result.set(f'上次结果：{exc}')

    def poll(self):
        current, now = pads(), time.monotonic()
        self.pad_text.set('手柄：' + (', '.join(f'编号 {i}，RT={v}' for i, v in current.items()) or '未检测到 XInput 设备'))
        if all(u.GetAsyncKeyState(k) & 0x8000 for k in (0x11, 0x12, 0x79)):
            self.stop()
        if self.armed:
            if now >= self.deadline or set(current) != set(self.previous):
                self.stop()
            else:
                for i, value in current.items():
                    if value > 60 and self.previous.get(i, 255) <= 60:
                        self.send()
                        break
        self.previous = current
        if self.due is not None:
            if now >= self.due:
                self.due = None
                self.send(self.test_mode)
            else:
                self.countdown_status()
        self.root.after(20, self.poll)

    def close(self):
        self.stop()
        self.root.destroy()

if __name__ == '__main__':
    if '--check' in sys.argv:
        print('Game windows:', [(h, pid(h), title(h), size(h)) for h in games()])
        print('XInput controllers:', pads())
    else:
        root = tk.Tk()
        App(root)
        root.mainloop()
