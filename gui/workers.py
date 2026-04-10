"""Background worker threads for Spyglass GUI."""

from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer
import logging


class SetupWorker(QObject):
    """Runs Spyglass setup steps (admin, config, DB) off the main thread."""
    step_completed = pyqtSignal(str, bool)  # (step_name, success)
    setup_finished = pyqtSignal(bool)       # overall success
    error_occurred = pyqtSignal(str)        # error message

    def __init__(self, spyglass):
        super().__init__()
        self.spyglass = spyglass

    def run_setup(self):
        steps = [
            ("admin", self.spyglass.verify_admin),
            ("config", self.spyglass.setup_config),
            ("database", self.spyglass.setup_db),
        ]
        for name, fn in steps:
            try:
                result = fn()
                self.step_completed.emit(name, result)
                if not result:
                    self.setup_finished.emit(False)
                    return
            except Exception as e:
                logging.error(f"Setup step '{name}' failed: {e}", exc_info=True)
                self.error_occurred.emit(f"{name}: {e}")
                self.setup_finished.emit(False)
                return

        self.setup_finished.emit(True)


class MonitoringWorker(QObject):
    """Periodically polls system stats and emits them as signals."""
    stats_updated = pyqtSignal(dict)   # cpu, memory, process count, etc.
    apps_updated = pyqtSignal(list)    # running apps list

    def __init__(self, spyglass):
        super().__init__()
        self.spyglass = spyglass
        self._running = False

    def start_polling(self):
        self._running = True
        self._poll()

    def stop_polling(self):
        self._running = False

    def _poll(self):
        if not self._running:
            return
        try:
            import psutil
            stats = {
                "cpu_percent": psutil.cpu_percent(interval=0.5),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used_gb": round(psutil.virtual_memory().used / (1024**3), 1),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            }
            self.stats_updated.emit(stats)

            if self.spyglass.app_monitor:
                apps = self.spyglass.app_monitor.get_running_apps()
                self.apps_updated.emit(apps or [])
        except Exception as e:
            logging.error(f"Monitoring poll error: {e}")

        if self._running:
            QTimer.singleShot(5000, self._poll)


class AlertSignalBridge(QObject):
    """Bridge between AlertEngine's thread and Qt main thread."""
    alert_raised = pyqtSignal(str, str, str)  # severity, alert_type, message
