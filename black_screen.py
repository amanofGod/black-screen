"""Win32 overlay. F10 toggle; F12 restore; Ctrl+Alt+F12 exit."""
import ctypes as C
from ctypes import wintypes as W
import sys
import time

u = C.WinDLL('user32', use_last_error=True)
k = C.WinDLL('kernel32', use_last_error=True)
g = C.WinDLL('gdi32', use_last_error=True)
m = None  # Load the optional cursor API only when first entering black screen.

def api(lib, name, args, result):
    fn = getattr(lib, name)
    fn.argtypes, fn.restype = args, result
    return fn

Proc = C.WINFUNCTYPE(C.c_ssize_t, W.HWND, W.UINT, W.WPARAM, W.LPARAM)
HookProc = C.WINFUNCTYPE(C.c_ssize_t, C.c_int, W.WPARAM, W.LPARAM)
class KeyboardEvent(C.Structure):
    _fields_ = [('key', W.DWORD), ('scan', W.DWORD), ('flags', W.DWORD),
                ('time', W.DWORD), ('extra', C.c_size_t)]

class RawDevice(C.Structure):
    _fields_ = [('page', W.WORD), ('usage', W.WORD), ('flags', W.DWORD), ('target', W.HWND)]

class RawHeader(C.Structure):
    _fields_ = [('kind', W.DWORD), ('size', W.DWORD), ('device', W.HANDLE), ('param', W.WPARAM)]

class RawKey(C.Structure):
    _fields_ = [('scan', W.WORD), ('flags', W.WORD), ('reserved', W.WORD),
                ('key', W.WORD), ('message', W.UINT), ('extra', W.DWORD)]

class WC(C.Structure):
    _fields_ = [('style', W.UINT), ('proc', Proc), ('cls', C.c_int), ('wnd', C.c_int),
                ('instance', W.HINSTANCE), ('icon', W.HICON), ('cursor', W.HANDLE),
                ('brush', W.HBRUSH), ('menu', W.LPCWSTR), ('name', W.LPCWSTR)]

api(k, 'GetModuleHandleW', [W.LPCWSTR], W.HMODULE)
api(k, 'CreateMutexW', [W.LPVOID, W.BOOL, W.LPCWSTR], W.HANDLE)
api(k, 'WaitForSingleObject', [W.HANDLE, W.DWORD], W.DWORD)
api(k, 'ReleaseMutex', [W.HANDLE], W.BOOL)
api(k, 'CloseHandle', [W.HANDLE], W.BOOL)
api(g, 'GetStockObject', [C.c_int], W.HANDLE)
api(u, 'RegisterClassW', [C.POINTER(WC)], W.WORD)
api(u, 'UnregisterClassW', [W.LPCWSTR, W.HINSTANCE], W.BOOL)
api(u, 'CreateWindowExW', [W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD, C.c_int, C.c_int,
    C.c_int, C.c_int, W.HWND, W.HMENU, W.HINSTANCE, W.LPVOID], W.HWND)
api(u, 'DefWindowProcW', [W.HWND, W.UINT, W.WPARAM, W.LPARAM], C.c_ssize_t)
api(u, 'SetLayeredWindowAttributes', [W.HWND, W.DWORD, W.BYTE, W.DWORD], W.BOOL)
api(u, 'SetWindowPos', [W.HWND, W.HWND, C.c_int, C.c_int, C.c_int, C.c_int, W.UINT], W.BOOL)
api(u, 'ShowWindow', [W.HWND, C.c_int], W.BOOL)
api(u, 'SetWindowsHookExW', [C.c_int, HookProc, W.HINSTANCE, W.DWORD], W.HANDLE)
api(u, 'CallNextHookEx', [W.HANDLE, C.c_int, W.WPARAM, W.LPARAM], C.c_ssize_t)
api(u, 'UnhookWindowsHookEx', [W.HANDLE], W.BOOL)
api(u, 'PostMessageW', [W.HWND, W.UINT, W.WPARAM, W.LPARAM], W.BOOL)
api(u, 'FindWindowW', [W.LPCWSTR, W.LPCWSTR], W.HWND)
api(u, 'RegisterRawInputDevices', [C.POINTER(RawDevice), W.UINT, W.UINT], W.BOOL)
api(u, 'GetRawInputData', [W.HANDLE, W.UINT, W.LPVOID, C.POINTER(W.UINT), W.UINT], W.UINT)
api(u, 'SendMessageTimeoutW', [W.HWND, W.UINT, W.WPARAM, W.LPARAM, W.UINT, W.UINT, C.POINTER(C.c_size_t)], W.LPARAM)
api(u, 'GetAsyncKeyState', [C.c_int], C.c_short)
api(u, 'SetTimer', [W.HWND, C.c_size_t, W.UINT, C.c_void_p], C.c_size_t)
api(u, 'KillTimer', [W.HWND, C.c_size_t], W.BOOL)
api(u, 'GetMessageW', [C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT], C.c_int)
api(u, 'PeekMessageW', [C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT, W.UINT], W.BOOL)
api(u, 'TranslateMessage', [C.POINTER(W.MSG)], W.BOOL)
api(u, 'DispatchMessageW', [C.POINTER(W.MSG)], C.c_ssize_t)
api(u, 'PostQuitMessage', [C.c_int], None)
api(u, 'DestroyWindow', [W.HWND], W.BOOL)
api(u, 'IsWindow', [W.HWND], W.BOOL)
api(u, 'IsWindowVisible', [W.HWND], W.BOOL)
api(u, 'GetForegroundWindow', [], W.HWND)
api(u, 'GetWindowThreadProcessId', [W.HWND, C.POINTER(W.DWORD)], W.DWORD)
api(u, 'GetCursorPos', [C.POINTER(W.POINT)], W.BOOL)
api(u, 'GetSystemMetrics', [C.c_int], C.c_int)
api(u, 'GetWindowRect', [W.HWND, C.POINTER(W.RECT)], W.BOOL)
api(u, 'GetWindowLongW', [W.HWND, C.c_int], W.LONG)
api(u, 'GetWindow', [W.HWND, W.UINT], W.HWND)
api(u, 'WindowFromPoint', [W.POINT], W.HWND)
api(u, 'MessageBoxW', [W.HWND, W.LPCWSTR, W.LPCWSTR, W.UINT], C.c_int)
api(u, 'SetProcessDpiAwarenessContext', [W.HANDLE], W.BOOL)

# Layered + transparent is required for cross-process mouse pass-through.
STYLE = 0x00080000 | 0x00000020 | 0x08000000 | 0x00000080
CLASS = 'LkwgVirtualBlackScreenV1'
WM_TOGGLE, WM_STATUS, WM_RESTORE, WM_REARM = 0x8001, 0x8002, 0x8003, 0x8004
WM_TIMER, WM_CLOSE = 0x113, 0x10

def check(result):
    if not result:
        raise C.WinError(C.get_last_error())
    return result

def bounds():
    return tuple(u.GetSystemMetrics(i) for i in (76, 77, 78, 79))


def magnification():
    global m
    if m is None:
        m = C.WinDLL('Magnification', use_last_error=True)
        api(m, 'MagInitialize', [], W.BOOL)
        api(m, 'MagUninitialize', [], W.BOOL)
        api(m, 'MagShowSystemCursor', [W.BOOL], W.BOOL)
    return m


class CursorVisibility:
    """Change only runtime cursor visibility, without replacing cursor shapes."""
    def __init__(self):
        self.initialized = False
        self.hidden = False

    def initialize(self):
        if not self.initialized:
            check(magnification().MagInitialize())
            self.initialized = True

    def hide(self):
        self.initialize()
        # Mark before calling, so partial failures still attempt restoration.
        self.hidden = True
        check(m.MagShowSystemCursor(False))

    def restore(self):
        if self.hidden:
            check(m.MagShowSystemCursor(True))
            self.hidden = False

    def close(self):
        try:
            self.restore()
        finally:
            if self.initialized:
                m.MagUninitialize()
                self.initialized = False

class Overlay:
    def __init__(self):
        self.hwnd = None
        self.atom = None
        self.visible = False
        self.cursor = CursorVisibility()
        self.hook = None
        self.hook_down = False
        self.poll_down = False
        self.poll_f12_down = False
        self.raw_down = False
        self.raw_registered = False
        self.detections = [0, 0, 0]  # F10 only: hook, Raw Input, state polling
        self.toggle_count = 0
        self.last_raise = 0
        self.last_toggle = float('-inf')
        self.last_input_check = 0
        self.next_input_refresh = 0
        self.foreground_thread = 0
        self.raw_buffer = C.create_string_buffer(64)
        self.timer = 0
        self.error = None
        self.instance = k.GetModuleHandleW(None)
        self.callback = Proc(self.handle)
        self.key_callback = HookProc(self.keyboard)
        try:
            wc = WC()
            wc.proc, wc.name, wc.instance = self.callback, CLASS, self.instance
            wc.brush = g.GetStockObject(4)  # BLACK_BRUSH, system-owned
            self.atom = check(u.RegisterClassW(C.byref(wc)))
            self.hwnd = check(u.CreateWindowExW(STYLE, CLASS, '洛克虚拟黑屏 F10 v5',
                0x80000000, 0, 0, 1, 1, None, None, self.instance, None))
            check(u.SetLayeredWindowAttributes(self.hwnd, 0, 255, 2))
            self.refresh_input()
            self.timer = check(u.SetTimer(self.hwnd, 1, 50, None))
        except Exception:
            self.close()
            raise

    def position(self):
        x, y, width, height = bounds()
        if width <= 0 or height <= 0:
            raise RuntimeError('无法读取显示器范围')
        check(u.SetWindowPos(self.hwnd, W.HWND(-1), x, y, width, height, 0x10 | 0x40))

    def toggle(self):
        if self.visible:
            self.restore_display()
        else:
            try:
                self.cursor.hide()
                self.position()
            except Exception:
                self.cursor.close()
                raise
            self.visible = True
            self.toggle_count += 1

    def restore_display(self):
        was_visible = self.visible
        u.ShowWindow(self.hwnd, 0)
        self.visible = False
        try:
            self.cursor.close()
        finally:
            # Shrink the hidden layered surface instead of retaining a full-screen buffer.
            check(u.SetWindowPos(self.hwnd, None, 0, 0, 1, 1, 0x10 | 0x4 | 0x2 | 0x100))
        if was_visible:
            self.toggle_count += 1

    def refresh_input(self):
        previous = self.hook
        self.hook = check(u.SetWindowsHookExW(13, self.key_callback, self.instance, 0))
        if previous:
            u.UnhookWindowsHookEx(previous)  # A timed-out hook may already be gone.
        device = RawDevice(1, 6, 0x100, self.hwnd)
        check(u.RegisterRawInputDevices(C.byref(device), 1, C.sizeof(device)))
        self.raw_registered = True
        down = bool(u.GetAsyncKeyState(0x79) & 0x8000)
        self.hook_down = self.raw_down = self.poll_down = down
        self.poll_f12_down = bool(u.GetAsyncKeyState(0x7B) & 0x8000)
        self.foreground_thread = u.GetWindowThreadProcessId(u.GetForegroundWindow(), None)
        self.next_input_refresh = time.monotonic() + 30

    def maintain_input(self):
        now = time.monotonic()
        if now - self.last_input_check < 0.5:
            return
        self.last_input_check = now
        foreground = u.GetWindowThreadProcessId(u.GetForegroundWindow(), None)
        if foreground != self.foreground_thread or now >= self.next_input_refresh:
            self.refresh_input()

    def f12_message(self):
        exit_requested = all(u.GetAsyncKeyState(key) & 0x8000 for key in (0x11, 0x12))
        return WM_CLOSE if exit_requested else WM_RESTORE

    def maintain_topmost(self):
        now = time.monotonic()
        if self.visible and now - self.last_raise >= 0.1:
            self.cursor.hide()
            check(u.SetWindowPos(self.hwnd, W.HWND(-1), 0, 0, 0, 0, 0x10 | 0x1 | 0x2 | 0x200))
            self.last_raise = now

    def request_toggle(self):
        # Hook and state polling may both see one press. Deduplicate their requests.
        now = time.monotonic()
        if now - self.last_toggle >= 0.25:
            self.toggle()
            # Initial cursor setup can be slow; queued copies are still the same press.
            self.last_toggle = time.monotonic()

    def keyboard(self, code, message, address):
        if code == 0:
            try:
                key = C.cast(address, C.POINTER(KeyboardEvent)).contents.key
                down = message in (0x100, 0x104)
                up = message in (0x101, 0x105)
                if key == 0x79 and (down or up):
                    if down and not self.hook_down:
                        self.detections[0] += 1
                        check(u.PostMessageW(self.hwnd, WM_TOGGLE, 0, 0))
                    self.hook_down = down
                    # Do not suppress F10: suppression also starves our state/Raw Input fallback.
                    return u.CallNextHookEx(self.hook, code, message, address)
                if key == 0x7B and (down or up):
                    if down:
                        check(u.PostMessageW(self.hwnd, self.f12_message(), 0, 0))
                    return 1
            except Exception as exc:
                self.error = exc
                u.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)
        return u.CallNextHookEx(self.hook, code, message, address)

    def poll_keys(self):
        f12_down = bool(u.GetAsyncKeyState(0x7B) & 0x8000)
        if f12_down and not self.poll_f12_down:
            u.PostMessageW(self.hwnd, self.f12_message(), 0, 0)
        self.poll_f12_down = f12_down
        down = bool(u.GetAsyncKeyState(0x79) & 0x8000)
        if down and not self.poll_down:
            self.detections[2] += 1
            self.request_toggle()
        self.poll_down = down
        if not down:
            self.hook_down = self.raw_down = False

    def raw_key(self, key, down):
        if key == 0x79:
            if down and not self.raw_down:
                self.detections[1] += 1
                self.request_toggle()
            self.raw_down = down
        elif key == 0x7B and down:
            u.PostMessageW(self.hwnd, self.f12_message(), 0, 0)

    def raw_input(self, handle):
        length = W.UINT()
        header_size = C.sizeof(RawHeader)
        if u.GetRawInputData(handle, 0x10000003, None, C.byref(length), header_size) == 0xffffffff:
            return
        if length.value < header_size + C.sizeof(RawKey):
            return
        if len(self.raw_buffer) < length.value:
            self.raw_buffer = C.create_string_buffer(length.value)
        buffer = self.raw_buffer
        count = u.GetRawInputData(handle, 0x10000003, buffer, C.byref(length), header_size)
        if count == 0xffffffff or count < header_size + C.sizeof(RawKey):
            return
        if RawHeader.from_buffer(buffer).kind == 1:
            event = RawKey.from_buffer(buffer, header_size)
            self.raw_key(event.key, not bool(event.flags & 1))

    def handle(self, hwnd, msg, wp, lp):
        try:
            if msg == WM_TOGGLE:
                self.request_toggle()
                return 0
            if msg == WM_TIMER and wp == 1:
                self.poll_keys()
                if u.IsWindow(hwnd):
                    self.maintain_topmost()
                    self.maintain_input()
                return 0
            if msg in (WM_RESTORE, WM_REARM):
                self.restore_display()
                self.refresh_input()
                return 0
            if msg == 0xff:  # WM_INPUT; DefWindowProc releases foreground input resources.
                self.raw_input(lp)
                return u.DefWindowProcW(hwnd, msg, wp, lp)
            if msg == WM_STATUS:
                fields = [int(self.visible), *self.detections, self.toggle_count, int(self.cursor.hidden)]
                return sum(min(n, 255) << (8 * index) for index, n in enumerate(fields))
            if msg == 0x7E and self.visible:  # WM_DISPLAYCHANGE
                self.position()
                return 0
            if msg == 0x21:  # WM_MOUSEACTIVATE, extra safeguard
                return 3  # MA_NOACTIVATE
            if msg == WM_CLOSE:
                u.DestroyWindow(hwnd)
                return 0
            if msg == 2:  # WM_DESTROY
                u.PostQuitMessage(0)
                return 0
            return u.DefWindowProcW(hwnd, msg, wp, lp)
        except Exception as exc:
            self.error = exc
            u.ShowWindow(hwnd, 0)
            u.PostQuitMessage(1)
            return 0

    def run(self):
        msg = W.MSG()
        while True:
            result = u.GetMessageW(C.byref(msg), None, 0, 0)
            if result == -1:
                raise C.WinError(C.get_last_error())
            if result == 0:
                break
            u.TranslateMessage(C.byref(msg))
            u.DispatchMessageW(C.byref(msg))
        if self.error:
            raise self.error

    def close(self):
        if self.raw_registered:
            device = RawDevice(1, 6, 1, None)
            u.RegisterRawInputDevices(C.byref(device), 1, C.sizeof(device))
            self.raw_registered = False
        if self.hook:
            u.UnhookWindowsHookEx(self.hook)
            self.hook = None
        if self.hwnd and u.IsWindow(self.hwnd):
            u.ShowWindow(self.hwnd, 0)
            if self.timer:
                u.KillTimer(self.hwnd, self.timer)
            u.DestroyWindow(self.hwnd)
        self.hwnd = None
        if self.atom:
            u.UnregisterClassW(CLASS, self.instance)
            self.atom = None
        self.cursor.close()


def verify(app):
    from unittest.mock import patch
    hwnd = app.hwnd
    assert not u.IsWindowVisible(hwnd)
    assert not app.cursor.hidden
    assert u.GetWindowLongW(hwnd, -20) & STYLE == STYLE
    foreground = u.GetForegroundWindow()
    cursor = W.POINT()
    check(u.GetCursorPos(C.byref(cursor)))
    def drain():
        msg = W.MSG()
        while u.PeekMessageW(C.byref(msg), None, 0, 0, 1):
            u.TranslateMessage(C.byref(msg))
            u.DispatchMessageW(C.byref(msg))

    event = KeyboardEvent()
    event.key = 0x79
    address = C.addressof(event)
    def control_event(message):
        with patch.object(u, 'CallNextHookEx', return_value=77):
            return app.keyboard(0, message, address)
    assert control_event(0x100) == 77
    drain()
    assert app.error is None
    assert app.visible and u.IsWindowVisible(hwnd)
    assert app.cursor.initialized and app.cursor.hidden
    for _ in range(5):
        assert control_event(0x100) == 77
    drain()
    assert app.visible, 'Repeated keydown toggled overlay'
    with patch.object(u, 'GetAsyncKeyState', side_effect=lambda key: -32768 if key == 0x79 else 0):
        app.poll_keys()
        app.poll_keys()
    assert app.visible, 'Hook and polling double-toggled one press'
    # Paint the real native window without sending any input to underlying apps.
    msg = W.MSG()
    end = time.monotonic() + 0.2
    while time.monotonic() < end:
        while u.PeekMessageW(C.byref(msg), None, 0, 0, 1):
            u.TranslateMessage(C.byref(msg))
            u.DispatchMessageW(C.byref(msg))
        time.sleep(0.01)
    assert foreground == u.GetForegroundWindow(), 'Foreground changed'
    after = W.POINT()
    check(u.GetCursorPos(C.byref(after)))
    assert (cursor.x, cursor.y) == (after.x, after.y), 'Cursor changed during test'
    rect = W.RECT()
    check(u.GetWindowRect(hwnd, C.byref(rect)))
    assert (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top) == bounds()
    assert u.WindowFromPoint(cursor) != hwnd, 'Overlay captured hit test'
    assert control_event(0x101) == 77
    with patch.object(u, 'GetAsyncKeyState', return_value=0):
        app.poll_keys()
    time.sleep(.26)
    # With no hook notification, state polling must still restore the display.
    with patch.object(u, 'GetAsyncKeyState', side_effect=lambda key: -32768 if key == 0x79 else 0):
        app.poll_keys()
        app.poll_keys()
    assert not app.visible and not u.IsWindowVisible(hwnd)
    assert not app.cursor.hidden, 'Cursor not restored with display'
    assert not app.cursor.initialized, 'Magnification resources retained while idle'
    small = W.RECT()
    check(u.GetWindowRect(hwnd, C.byref(small)))
    assert (small.right - small.left, small.bottom - small.top) == (1, 1)
    app.toggle()
    assert app.visible and u.IsWindowVisible(hwnd)
    # Simulate a competing topmost desktop widget, then restore the overlay's order.
    rival = check(u.CreateWindowExW(0x08000008, 'Static', 'Local topmost verification',
        0x80000006, 30, 30, 100, 60, None, None, app.instance, None))
    try:
        check(u.SetWindowPos(rival, W.HWND(-1), 30, 30, 100, 60, 0x10 | 0x40))
        app.last_raise = 0
        app.maintain_topmost()
        above = u.GetWindow(rival, 3)  # GW_HWNDPREV
        found = False
        while above:
            if above == hwnd:
                found = True
                break
            above = u.GetWindow(above, 3)
        assert found, 'Overlay did not cover a competing topmost window'
        assert foreground == u.GetForegroundWindow(), 'Z-order maintenance activated overlay'
    finally:
        u.DestroyWindow(rival)
    before = app.toggle_count
    app.raw_key(0x41, True)
    assert app.toggle_count == before
    app.last_toggle = float('-inf')
    # Use a complete native Raw Input keyboard buffer to verify parsing and edges.
    raw_size = C.sizeof(RawHeader) + C.sizeof(RawKey)
    raw_data = C.create_string_buffer(raw_size)
    raw_header = RawHeader.from_buffer(raw_data)
    raw_header.kind, raw_header.size = 1, raw_size
    raw_event = RawKey.from_buffer(raw_data, C.sizeof(RawHeader))
    raw_event.key = 0x79
    def fake_raw(handle, command, buffer, length, header_size):
        C.cast(length, C.POINTER(W.UINT))[0] = raw_size
        if buffer is None:
            return 0
        C.memmove(buffer, raw_data, raw_size)
        return raw_size
    with patch.object(u, 'GetRawInputData', side_effect=fake_raw):
        app.raw_input(1)
        app.raw_input(1)
        assert not app.visible and app.toggle_count == before + 1
        raw_event.flags = 1
        app.raw_input(1)
        assert not app.raw_down
    assert app.detections[1] == 1
    app.toggle()
    app.toggle()
    with patch.object(m, 'MagShowSystemCursor', side_effect=[0, 1]) as cursor_api:
        try:
            app.toggle()
            raise AssertionError('Cursor hide failure ignored')
        except OSError:
            pass
        assert not app.visible and not app.cursor.hidden
        assert [call.args[0] for call in cursor_api.call_args_list] == [False, True]
    with patch.object(app, 'position', side_effect=RuntimeError('Window display failed')):
        try:
            app.toggle()
            raise AssertionError('Window display failure ignored')
        except RuntimeError as exc:
            assert str(exc) == 'Window display failed'
        assert not app.visible and not app.cursor.hidden, 'Display failure left cursor hidden'
    app.toggle()
    with patch.object(u, 'CallNextHookEx', return_value=123) as next_hook:
        event.key = 0x41
        assert app.keyboard(0, 0x100, address) == 123
        assert app.keyboard(-1, 0x100, 0) == 123
        assert next_hook.call_count == 2
    event.key = 0x7B
    assert app.keyboard(0, 0x100, address) == 1
    drain()
    assert u.IsWindow(hwnd) and not app.visible, 'F12 must restore without exiting'
    assert not app.cursor.hidden and not app.cursor.initialized
    for _ in range(3):
        event.key = 0x79
        app.last_toggle = float('-inf')
        assert control_event(0x100) == 77
        drain()
        assert app.visible, 'F10 did not work after F12'
        control_event(0x101)
        event.key = 0x7B
        assert app.keyboard(0, 0x100, address) == 1
        drain()
        assert u.IsWindow(hwnd) and not app.visible
    # Front-end/game thread changes and a lost hook must be repairable.
    old_hook = app.hook
    app.last_input_check = float('-inf')
    with patch.object(u, 'GetWindowThreadProcessId', return_value=98765):
        app.maintain_input()
        assert app.foreground_thread == 98765 and app.hook != old_hook
    check(u.UnhookWindowsHookEx(app.hook))
    app.next_input_refresh = 0
    app.last_input_check = float('-inf')
    app.maintain_input()
    assert app.hook
    app.handle(hwnd, WM_REARM, 0, 0)
    assert u.IsWindow(hwnd) and not app.visible, 'Instance reuse failed'
    with patch.object(u, 'GetAsyncKeyState', side_effect=lambda key: -32768 if key in (0x11, 0x12) else 0):
        assert app.keyboard(0, 0x100, address) == 1
        drain()
    assert not u.IsWindow(hwnd), 'Ctrl+Alt+F12 did not exit'
    assert foreground == u.GetForegroundWindow()
    app.close()
    assert app.hook is None, 'Hook not released'
    assert not app.raw_registered, 'Raw Input not released'
    assert not app.cursor.hidden and not app.cursor.initialized, 'Cursor visibility not restored/cleaned'
    print('PASS: F10/F12 repeated reuse; F12 stays resident; Ctrl+Alt+F12 exits; front-end change/lost hook repair; reused instance rearm; 1x1 idle surface; Magnification released; cursor/failure recovery; Raw Input/dedup; topmost and focus preserved.')


def main():
    # Only changes this process, not Windows display settings.
    u.SetProcessDpiAwarenessContext(W.HANDLE(-4))
    app = None
    mutex = None
    mutex_owned = False
    try:
        if '--restore-cursor' in sys.argv:
            cursor = CursorVisibility()
            try:
                cursor.initialize()
                cursor.hidden = True
                cursor.restore()
            finally:
                cursor.close()
            print('System cursor display restored')
            return
        if '--status' in sys.argv:
            hwnd = u.FindWindowW(CLASS, None)
            if not hwnd:
                print('Not running')
                return
            result = C.c_size_t()
            check(u.SendMessageTimeoutW(hwnd, WM_STATUS, 0, 0, 2, 1000, C.byref(result)))
            values = [(result.value >> (8 * n)) & 255 for n in range(6)]
            print(dict(zip(('visible', 'hook_f10', 'raw_f10', 'poll_f10', 'toggles', 'cursor_hidden'), values)))
            return
        mutex = check(k.CreateMutexW(None, False, 'Local\\LkwgVirtualBlackScreenSingleInstance'))
        wait = k.WaitForSingleObject(mutex, 0)
        if wait in (0, 0x80):
            mutex_owned = True
        elif wait != 0x102:
            raise C.WinError(C.get_last_error())
        existing = u.FindWindowW(CLASS, None)
        if not mutex_owned and not existing:
            deadline = time.monotonic() + 3
            while not existing and time.monotonic() < deadline:
                time.sleep(0.05)
                existing = u.FindWindowW(CLASS, None)
            if not existing:
                raise RuntimeError('黑屏程序正在启动或退出，稍后重试。')
        if existing:
            if '--verify' in sys.argv:
                raise RuntimeError('验证前请先退出正在运行的黑屏程序。')
            result = C.c_size_t()
            check(u.SendMessageTimeoutW(existing, WM_REARM, 0, 0, 2, 2000, C.byref(result)))
            return
        app = Overlay()
        if '--verify' in sys.argv:
            verify(app)
        else:
            if '--quiet' not in sys.argv:
                u.MessageBoxW(None, '虚拟黑屏 v5 已启动。\n\nF10：黑屏／恢复。\nF12：恢复画面和指针，程序保留。\nCtrl+Alt+F12：完全退出。\n\n重复启动会复用已有程序。', '洛克虚拟黑屏 v5', 0x40)
            app.run()
    finally:
        try:
            if app:
                app.close()
        finally:
            if mutex:
                if mutex_owned:
                    k.ReleaseMutex(mutex)
                k.CloseHandle(mutex)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        if '--verify' in sys.argv:
            raise
        u.MessageBoxW(None, str(exc), '黑屏程序未运行／已退出', 0x10)
        sys.exit(1)
