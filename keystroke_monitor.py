from collections import deque
import datetime
import logging
import threading
import time
from pynput import keyboard
from typing import Dict, Optional

from pynput import keyboard
from alert_manager import AlertManager
from threshold_engine import ThresholdEngine


class KeystrokeMonitor:
    def __init__(
        self,
        time_interval: int = 60,
        log_file: str = "keystrokes.log",
        alert_manager: Optional[AlertManager] = None,
        monitoring_level: str = "MEDIUM",
    ):
        print("Initializing KeystrokeMonitor...")

        self.running = False
        self.time_interval = time_interval
        self.log_file = log_file
        self.keystrokes: Dict[str, int] = {}
        self.lock = threading.Lock()
        self.interval_start = datetime.datetime.now()
        self.listener: Optional[keyboard.Listener] = None
        self.last_key: Optional[str] = None

        self.monitoring_level = monitoring_level
        self.threshold_engine = ThresholdEngine(monitoring_level)
        all_thresholds = self.threshold_engine.get_thresholds()
        self.thresholds = all_thresholds["keystroke"]
        alerting = all_thresholds["alerting"]
        self.alert_manager = alert_manager or AlertManager(
            cooldown_seconds=alerting["cooldown_seconds"],
            startup_grace_seconds=alerting["startup_grace_seconds"],
        )

        self.key_timestamps = deque()
        self.last_key_time: Optional[float] = None
        self.continuous_start_time: Optional[float] = None
        self.last_mouse_position = self._get_mouse_position()
        self.last_mouse_move_time = time.time()
        self.mouse_thread: Optional[threading.Thread] = None

    def _get_mouse_position(self):
        try:
            import ctypes
            from ctypes import wintypes

            class POINT(ctypes.Structure):
                _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

            point = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
            return (point.x, point.y)
        except Exception:
            return None

    def _mouse_monitor_loop(self):
        poll_interval = self.thresholds.get("mouse_poll_interval_seconds", 1)
        while self.running:
            try:
                pos = self._get_mouse_position()
                if pos is not None and pos != self.last_mouse_position:
                    self.last_mouse_position = pos
                    self.last_mouse_move_time = time.time()
                time.sleep(poll_interval)
            except Exception:
                time.sleep(poll_interval)

    def _get_foreground_title(self) -> str:
        try:
            import ctypes

            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if hwnd == 0:
                return ""

            length = user32.GetWindowTextLengthW(hwnd) + 1
            title_buffer = ctypes.create_unicode_buffer(length)
            user32.GetWindowTextW(hwnd, title_buffer, length)
            return title_buffer.value.strip()
        except Exception:
            return ""

    def on_press(self, key):
        current_time = time.time()

        try:
            key_str = key.char
        except AttributeError:
            key_str = str(key)

        with self.lock:
            self.keystrokes[key_str] = self.keystrokes.get(key_str, 0) + 1
            self.last_key = key_str
        logging.getLogger('keystrokes').info(f"Key: {key_str}")
        
    def on_click(self, x,y):
        with self.lock:
            self.keystrokes['Mouse Click'] = self.keystrokes.get('Mouse Click', 0) + 1
    
    def updateLog(self, string: str):
        self.interval_start = datetime.datetime.now()
        with open(self.log_file, "a", encoding="utf-8") as l:
            l.write(f"{self.interval_start} - {string}\n")

    def updateDatabase(self, key):
        with self.lock:
            self.keystrokes.clear()

    def startLog(self) -> bool:
        if self.running:
            print("Keystroke Monitor is already running.")
            return False

        print("Starting Keystroke Monitor...")
        self.running = True
        self.key_timestamps.clear()
        self.last_key_time = None
        self.continuous_start_time = None
        self.last_mouse_position = self._get_mouse_position()
        self.last_mouse_move_time = time.time()

        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

        self.mouse_thread = threading.Thread(target=self._mouse_monitor_loop, daemon=True, name="MouseMonitor")
        self.mouse_thread.start()
        return True

    def stopLog(self):
        if not self.running:
            print("Keystroke Monitor is not running.")
            return

        print("Stopping Keystroke Monitor...")
        self.running = False
        if self.listener:
            self.listener.stop()

        self.updateLog(f"Keystrokes: {self.keystrokes}")
        self.updateDatabase(self.keystrokes)
        print("Keystroke Monitor stopped and data logged.")
