import logging
import threading
import time
import ctypes
from typing import Dict, Optional, Any


class AlertManager:
    def __init__(
        self,
        database=None,
        monitoring_level: str = "MEDIUM",
        cooldown_seconds: int = 90,
        startup_grace_seconds: int = 30,
        popup_enabled: bool = True,
    ):
        self.database = database
        self.monitoring_level = monitoring_level
        self.cooldown_seconds = max(1, int(cooldown_seconds))
        self.startup_grace_seconds = max(0, int(startup_grace_seconds))
        self.popup_enabled = popup_enabled
        self.started_at = time.time()
        self._last_alert_times: Dict[str, float] = {}
        self._lock = threading.Lock()

    def can_trigger(self, key: str) -> bool:
        now = time.time()
        if now - self.started_at < self.startup_grace_seconds:
            return False
        with self._lock:
            last_time = self._last_alert_times.get(key, 0.0)
            if now - last_time < self.cooldown_seconds:
                return False
            self._last_alert_times[key] = now
        return True

    def trigger_alert(
        self,
        category: str,
        message: str,
        severity: str = "medium",
        module: str = "system",
        key: Optional[str] = None,
        app_name: str = "Unknown",
        threshold_name: Optional[str] = None,
        threshold_value: Optional[float] = None,
        observed_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        dedupe_key = key or f"{module}:{category}:{app_name}".lower()
        if not self.can_trigger(dedupe_key):
            return False

        logging.warning(
            "[ALERT] %s | severity=%s | module=%s | app=%s | threshold=%s=%s | observed=%s | %s",
            category,
            severity,
            module,
            app_name,
            threshold_name,
            threshold_value,
            observed_value,
            message,
        )
        self._show_popup(category, severity, app_name, message)
        return True

    def _show_popup(self, category: str, severity: str, app_name: str, message: str) -> None:
        if not self.popup_enabled:
            return

        popup_text = (
            f"SpyGlass Alert\n\n"
            f"Category: {category}\n"
            f"Severity: {severity.upper()}\n"
            f"Application: {app_name}\n\n"
            f"{message}"
        )

        def _popup():
            try:
                ctypes.windll.user32.MessageBoxW(0, popup_text, "SpyGlass Alert", 0x1000)
            except Exception as exc:
                logging.debug("Popup display failed: %s", exc)

        threading.Thread(target=_popup, daemon=True).start()
