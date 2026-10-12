import ctypes as C
from ctypes import wintypes as W
import background_input as b
from unittest.mock import patch

u = b.u
Proc = C.WINFUNCTYPE(C.c_ssize_t, W.HWND, W.UINT, W.WPARAM, W.LPARAM)
class WC(C.Structure):
    _fields_ = [('style', W.UINT), ('proc', Proc), ('cls', C.c_int), ('wnd', C.c_int),
                ('instance', W.HINSTANCE), ('icon', W.HICON), ('cursor', W.HANDLE),
                ('brush', W.HBRUSH), ('menu', W.LPCWSTR), ('name', W.LPCWSTR)]
b.api('DefWindowProcW', [W.HWND, W.UINT, W.WPARAM, W.LPARAM], C.c_ssize_t)
b.api('RegisterClassW', [C.POINTER(WC)], W.WORD)
b.api('CreateWindowExW', [W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD,
    C.c_int, C.c_int, C.c_int, C.c_int, W.HWND, W.HMENU, W.HINSTANCE, W.LPVOID], W.HWND)
b.api('DestroyWindow', [W.HWND], W.BOOL)
b.api('UnregisterClassW', [W.LPCWSTR, W.HINSTANCE], W.BOOL)
b.api('PeekMessageW', [C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT, W.UINT], W.BOOL)
b.api('DispatchMessageW', [C.POINTER(W.MSG)], C.c_ssize_t)
events = []
@Proc
def handler(hwnd, msg, wp, lp):
    if msg in (0x201, 0x202):
        events.append((msg, wp, lp))
        return 0
    return u.DefWindowProcW(hwnd, msg, wp, lp)
wc = WC()
wc.proc, wc.name = handler, 'LkwgBackgroundInputVerification'
assert u.RegisterClassW(C.byref(wc))
hwnd = None
try:
    hwnd = u.CreateWindowExW(0, wc.name, 'Local verification only', 0, 0, 0, 240, 180, None, None, None, None)
    assert hwnd
    target = b.Target(hwnd)
    before = W.POINT()
    u.GetCursorPos(C.byref(before))
    foreground = u.GetForegroundWindow()
    target.click()
    msg = W.MSG()
    while u.PeekMessageW(C.byref(msg), hwnd, 0, 0, 1):
        u.DispatchMessageW(C.byref(msg))
    assert [e[0] for e in events] == [0x201, 0x202], events
    assert [e[1] for e in events] == [1, 0], events
    expected = (target.size[0] // 2) | ((target.size[1] // 2) << 16)
    assert all(e[2] == expected for e in events)
    after = W.POINT()
    u.GetCursorPos(C.byref(after))
    assert (before.x, before.y) == (after.x, after.y), 'Cursor changed during test'
    assert foreground == u.GetForegroundWindow(), 'Foreground changed during test'
    def drain():
        while u.PeekMessageW(C.byref(msg), hwnd, 0, 0, 1):
            u.DispatchMessageW(C.byref(msg))
    for required, actual in ((True, None), (False, hwnd)):
        events.clear()
        with patch.object(u, 'GetForegroundWindow', return_value=actual):
            try:
                target.click(required)
                raise AssertionError('Wrong focus accepted')
            except RuntimeError as exc:
                assert '未发送点击' in str(exc)
        drain()
        assert events == [], 'Cancelled test still sent input'
    for required, actual in ((True, hwnd), (False, None)):
        events.clear()
        with patch.object(u, 'GetForegroundWindow', return_value=actual):
            assert target.click(required) == (required, required)
        drain()
        assert [e[0] for e in events] == [0x201, 0x202]
    with patch.object(u, 'GetForegroundWindow', side_effect=[hwnd, None]):
        assert target.click(True) == (True, False)
    drain()
    print('PASS: wrong focus cancels without input; front/back modes deliver same messages; focus changes reported.')
    target.size = (1, 1)
    try:
        target.click()
        raise AssertionError('Resized target accepted')
    except RuntimeError:
        pass
    u.DestroyWindow(hwnd)
    hwnd = None
    try:
        target.click()
        raise AssertionError('Destroyed target accepted')
    except RuntimeError:
        pass
    try:
        b.Target(0)
        raise AssertionError('Null target accepted')
    except RuntimeError:
        pass
    print('PASS: down/up delivered to local target; coordinates correct; cursor and foreground unchanged; resized/destroyed/null targets rejected.')
finally:
    if hwnd:
        u.DestroyWindow(hwnd)
    u.UnregisterClassW(wc.name, None)

import tkinter as tk
root = tk.Tk()
root.withdraw()
app = b.App(root)
assert not app.armed and app.due is None
app.last_result.set('preserved result')
app.stop()
assert app.last_result.get() == 'preserved result'
root.update()
app.close()
print('PASS: GUI starts stopped and closes cleanly. No game clicks sent.')
