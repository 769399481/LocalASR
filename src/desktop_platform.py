"""Native overlay/hotkey boundary. macOS intentionally reports unsupported."""
import sys
import queue
import threading


class DesktopPlatform:
    supports_click_through = sys.platform == "win32"
    supports_hotkeys = sys.platform == "win32"

    def __init__(self):
        self.registered = {}
        self.commands = queue.Queue(32)
        self.stop_event = threading.Event()
        self.thread = None
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            self.ctypes, self.wintypes = ctypes, wintypes
            self.user = ctypes.WinDLL("user32", use_last_error=True)
            self.user.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
            self.user.GetAncestor.restype = wintypes.HWND
            self.user.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
            self.user.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
            self.user.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
            self.user.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]

    def click_through(self, window, enabled):
        if not self.supports_click_through:
            return False
        window.update_idletasks()
        hwnd = self.user.GetAncestor(window.winfo_id(), 2)
        style = self.user.GetWindowLongW(hwnd, -20)
        bits = 0x20 | 0x08000000  # WS_EX_TRANSPARENT, WS_EX_NOACTIVATE
        self.ctypes.set_last_error(0)
        self.user.SetWindowLongW(hwnd, -20, (style | 0x80000 | bits) if enabled else (style & ~bits))
        if self.ctypes.get_last_error():
            raise OSError(self.ctypes.get_last_error(), "无法切换字幕鼠标穿透")
        return True

    def register(self):
        if not self.supports_hotkeys:
            return ["此平台尚未支持全局快捷键。"]
        self.close()
        self.stop_event.clear()
        self.ready = threading.Event()
        self.failures = []
        self.thread = threading.Thread(target=self._listen, name="global-hotkeys", daemon=True)
        self.thread.start()
        self.ready.wait(2)
        return self.failures if self.ready.is_set() else ["快捷键启动超时。"]

    def _listen(self):
        for identifier, key, action in ((0x4A11, "S", "start_stop"), (0x4A12, "H", "show_hide"),
                                        (0x4A13, "L", "language"), (0x4A14, "E", "edit")):
            if self.user.RegisterHotKey(None, identifier, 0x4003, ord(key)):
                self.registered[identifier] = action
            else:
                self.failures.append(f"Ctrl+Alt+{key} 已被占用，未注册。")
        self.ready.set()
        try:
            while not self.stop_event.wait(.02):
                msg = self.wintypes.MSG()
                while self.user.PeekMessageW(self.ctypes.byref(msg), None, 0x312, 0x312, 1):
                    if msg.wParam in self.registered:
                        try:
                            self.commands.put_nowait(self.registered[msg.wParam])
                        except queue.Full:
                            pass
        finally:
            for identifier in self.registered:
                self.user.UnregisterHotKey(None, identifier)
            self.registered.clear()

    def poll(self):
        actions = []
        while True:
            try:
                actions.append(self.commands.get_nowait())
            except queue.Empty:
                break
        return actions

    def close(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(2)
            if self.thread.is_alive():
                raise TimeoutError("Global hotkeys still stopping")
            self.thread = None
        self.poll()


def monitor_rect(window):
    """Nearest monitor work area; includes negative secondary-monitor coordinates."""
    if sys.platform != "win32":
        return 0, 0, window.winfo_screenwidth(), window.winfo_screenheight()
    import ctypes
    from ctypes import wintypes
    class MonitorInfo(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("monitor", wintypes.RECT),
                    ("work", wintypes.RECT), ("flags", wintypes.DWORD)]
    user = ctypes.WinDLL("user32")
    user.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    user.MonitorFromWindow.restype = wintypes.HANDLE
    user.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MonitorInfo)]
    info = MonitorInfo()
    info.size = ctypes.sizeof(info)
    user.GetMonitorInfoW(user.MonitorFromWindow(window.winfo_id(), 2), ctypes.byref(info))
    return info.work.left, info.work.top, info.work.right, info.work.bottom
def enable_dpi_awareness():
    """Best effort per-monitor DPI awareness before Tk creation."""
    import sys
    if sys.platform == 'win32':
        import ctypes
        try:
            ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except (AttributeError, OSError):
            pass

