import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
import sys
import psutil
import winreg

from database import updateAppTable
from alert_manager import AlertManager
from threshold_engine import ThresholdEngine


SAFE_PROCESS_NAMES = {
    "system idle process",
    "system",
    "registry",
    "searchapp.exe",
    "searchhost.exe",
    "textinputhost.exe",
    "lockapp.exe",
    "sihost.exe",
    "taskmgr.exe",
    "dwm.exe",
    "runtimebroker.exe",
    "svchost.exe",
    "explorer.exe",
    "python.exe",
    "pythonw.exe",
    "discord.exe",
    "chrome.exe",
    "msedge.exe",
    "firefox.exe",
    "steam.exe",
}

SAFE_PATH_KEYWORDS = (
    "\\windows\\",
    "c:\\program files",
    "c:\\program files (x86)",
    "\\appdata\\local\\discord",
    "\\appdata\\local\\google\\chrome",
    "\\appdata\\local\\microsoft\\edge",
)


class AppMonitor:
    def __init__(
        self,
        poll_interval: float = 15.0,
        monitoring_level: str = "MEDIUM",
        alert_manager: Optional[AlertManager] = None,
    ):
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.current_process: Optional[Dict[str, Any]] = None
        self.last_update: Optional[datetime] = None
        self.monitoring_level = monitoring_level
        self.threshold_engine = ThresholdEngine(monitoring_level)
        self.thresholds = self.threshold_engine.get_thresholds()
        self.poll_interval = float(self.thresholds["application"]["poll_interval_seconds"]) if poll_interval == 15.0 else poll_interval
        self.alert_manager = alert_manager or AlertManager(
            cooldown_seconds=self.thresholds["alerting"]["cooldown_seconds"],
            startup_grace_seconds=self.thresholds["alerting"]["startup_grace_seconds"],
        )
        self._app_cpu_duration: Dict[int, float] = {}
        self._background_cpu_duration: Dict[int, float] = {}
        self._system_cpu_duration = 0.0

    def start_monitoring(self) -> bool:
        if self.thread and self.thread.is_alive():
            print("Process monitoring is already running.")
            return True
        try:
            self.is_running = True
            self.thread = threading.Thread(target=self.monitor_loop, daemon=True, name="AppMonitor")
            self.thread.start()
            logging.info("App monitor thread started")
            return True
        except Exception as e:
            logging.error(f"Failed to start app monitor thread: {e}")
            return False

    def stop_monitoring(self) -> None:
        logging.info("Stopping app monitor...")
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
            logging.info("App monitor thread stopped")

    def monitor_loop(self) -> None:
        logging.info("Entering app monitor loop")
        while self.is_running:
            try:
                foreground = self.get_foreground_window()
                if foreground and foreground != self.current_process:
                    self.current_process = foreground
                    self.last_update = datetime.now()
                    logging.info("Active app changed: %s | %s", foreground["name"], foreground["window_title"])
                self.evaluate_thresholds(foreground)
                threading.Event().wait(self.poll_interval)
            except Exception as e:
                logging.error("Error in app monitor loop: %s", e, exc_info=True)

    def evaluate_thresholds(self, foreground: Optional[Dict[str, Any]]) -> None:
        thresholds = self.thresholds["application"]
        running_apps = self.get_running_apps()
        foreground_pid = foreground["pid"] if foreground else None

        process_count = len(running_apps)
        if process_count > thresholds["process_count"]:
            self.alert_manager.trigger_alert(
                category="System Overload",
                message=f"More than {thresholds['process_count']} processes are running simultaneously.",
                severity="medium",
                module="application",
                key="process_count",
                app_name="System",
                threshold_name="process_count",
                threshold_value=thresholds["process_count"],
                observed_value=process_count,
            )

        system_cpu = psutil.cpu_percent(interval=None)
        if system_cpu >= thresholds["system_cpu_percent"]:
            self._system_cpu_duration += self.poll_interval
        else:
            self._system_cpu_duration = 0.0

        if self._system_cpu_duration >= thresholds["system_cpu_duration_seconds"]:
            self.alert_manager.trigger_alert(
                category="System Performance Risk",
                message="Total CPU usage stayed above the configured threshold.",
                severity="high",
                module="application",
                key="system_cpu_duration",
                app_name="System",
                threshold_name="system_cpu_percent",
                threshold_value=thresholds["system_cpu_percent"],
                observed_value=system_cpu,
            )

        for app in running_apps:
            pid = app["pid"]
            app_name = app["name"]
            exe_path = app["exe_path"]
            cpu_percent = float(app["cpu_percent"] or 0.0)
            is_foreground = foreground_pid == pid
            is_safe = self._is_safe_process(app_name, exe_path)

            if self._is_spyglass_process(app_name):
                if cpu_percent >= thresholds["spyglass_cpu_percent"]:
                    self.alert_manager.trigger_alert(
                        category="Application Performance Issue",
                        message="SpyGlass is using more CPU than expected.",
                        severity="medium",
                        module="application",
                        key="spyglass_cpu",
                        app_name=app_name,
                        threshold_name="spyglass_cpu_percent",
                        threshold_value=thresholds["spyglass_cpu_percent"],
                        observed_value=cpu_percent,
                    )
                continue

            if not is_safe:
                if cpu_percent >= thresholds["app_cpu_percent"]:
                    self._app_cpu_duration[pid] = self._app_cpu_duration.get(pid, 0.0) + self.poll_interval
                else:
                    self._app_cpu_duration[pid] = 0.0

                if self._app_cpu_duration[pid] >= thresholds["app_cpu_duration_seconds"]:
                    self.alert_manager.trigger_alert(
                        category="Performance Risk",
                        message=f"{app_name} has exceeded the CPU threshold for an extended period.",
                        severity="high",
                        module="application",
                        key=f"app_cpu:{pid}",
                        app_name=app_name,
                        threshold_name="app_cpu_percent",
                        threshold_value=thresholds["app_cpu_percent"],
                        observed_value=cpu_percent,
                    )

                if not is_foreground and cpu_percent >= thresholds["background_cpu_percent"]:
                    self._background_cpu_duration[pid] = self._background_cpu_duration.get(pid, 0.0) + self.poll_interval
                else:
                    self._background_cpu_duration[pid] = 0.0

                if self._background_cpu_duration[pid] >= thresholds["background_cpu_duration_seconds"]:
                    self.alert_manager.trigger_alert(
                        category="Hidden Activity",
                        message=f"Background process {app_name} is using unusually high CPU.",
                        severity="high",
                        module="application",
                        key=f"background_cpu:{pid}",
                        app_name=app_name,
                        threshold_name="background_cpu_percent",
                        threshold_value=thresholds["background_cpu_percent"],
                        observed_value=cpu_percent,
                    )

            if self._is_unknown_app(app_name, exe_path):
                min_cpu = thresholds["unknown_app_min_cpu_percent"]
                if cpu_percent >= min_cpu:
                    self.alert_manager.trigger_alert(
                        category="Suspicious Application",
                        message=f"Unknown application detected with notable CPU usage: {app_name}",
                        severity="medium",
                        module="application",
                        key=f"unknown_app:{app_name.lower()}",
                        app_name=app_name,
                        threshold_name="unknown_app_min_cpu_percent",
                        threshold_value=min_cpu,
                        observed_value=cpu_percent,
                    )

                if system_cpu >= thresholds["system_cpu_percent"] and cpu_percent >= min_cpu:
                    self.alert_manager.trigger_alert(
                        category="Potential Malware",
                        message=f"High system CPU combined with unknown application activity: {app_name}",
                        severity="high",
                        module="application",
                        key=f"malware_combo:{app_name.lower()}",
                        app_name=app_name,
                        threshold_name="system_cpu_percent",
                        threshold_value=thresholds["system_cpu_percent"],
                        observed_value=system_cpu,
                    )

    def _is_spyglass_process(self, name: str) -> bool:
        value = (name or "").lower()
        return "spyglass" in value

    def _is_safe_process(self, app_name: str, exe_path: str) -> bool:
        app_name_l = (app_name or "").lower()
        exe_path_l = (exe_path or "").lower()
        if app_name_l in SAFE_PROCESS_NAMES:
            return True
        if exe_path_l in {"unknown", ""}:
            return False
        if any(keyword in exe_path_l for keyword in SAFE_PATH_KEYWORDS):
            return True
        return False

    def _is_unknown_app(self, app_name: str, exe_path: str) -> bool:
        app_name_l = (app_name or "").lower()
        exe_path_l = (exe_path or "").lower()
        if not app_name_l:
            return False
        if self._is_safe_process(app_name, exe_path):
            return False
        if exe_path_l in {"unknown", ""}:
            return False
        return True

    def get_foreground_window(self) -> Optional[Dict[str, Any]]:
        try:
            if sys.platform != "win32":
                return None
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if hwnd == 0:
                return None
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            length = user32.GetWindowTextLengthW(hwnd) + 1
            title_buffer = ctypes.create_unicode_buffer(length)
            user32.GetWindowTextW(hwnd, title_buffer, length)
            window_title = title_buffer.value
            process = psutil.Process(pid.value)
            return {
                "pid": process.pid,
                "name": process.name(),
                "exe_path": process.exe() if process.exe() else "Unknown",
                "window_title": window_title,
                "timestamp": datetime.now(),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
        except Exception as e:
            logging.error(f"Failed to get foreground window: {e}")
            return None

    def get_running_apps(self) -> List[Dict[str, Any]]:
        running_apps: List[Dict[str, Any]] = []
        try:
            for process in psutil.process_iter(["pid", "name", "exe", "status", "memory_info", "cpu_percent"]):
                try:
                    info = process.info
                    running_apps.append(
                        {
                            "pid": info.get("pid"),
                            "name": info.get("name") or "Unknown",
                            "exe_path": info.get("exe") or "Unknown",
                            "status": info.get("status") or "unknown",
                            "memory_mb": round((info.get("memory_info").rss / (1024 * 1024)), 2)
                            if info.get("memory_info")
                            else 0.0,
                            "cpu_percent": float(info.get("cpu_percent") or 0.0),
                            "window_title": "",
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return running_apps
        except Exception as e:
            logging.error(f"Error getting running apps: {e}")
            return running_apps

    def get_installed_apps(self) -> List[Dict[str, Any]]:
        installed_apps: List[Dict[str, Any]] = []
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        for hkey, path in registry_paths:
            try:
                registry_key = winreg.OpenKey(hkey, path)
                for i in range(winreg.QueryInfoKey(registry_key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(registry_key, i)
                        subkey = winreg.OpenKey(registry_key, subkey_name)
                        try:
                            name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        except FileNotFoundError:
                            winreg.CloseKey(subkey)
                            continue
                        try:
                            version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                        except FileNotFoundError:
                            version = "Unknown"
                        try:
                            vendor = winreg.QueryValueEx(subkey, "Publisher")[0]
                        except FileNotFoundError:
                            vendor = "Unknown"
                        try:
                            install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                        except FileNotFoundError:
                            install_location = "Unknown"
                        installed_apps.append(
                            {
                                "name": name,
                                "version": version,
                                "vendor": vendor,
                                "install_location": install_location,
                            }
                        )
                        winreg.CloseKey(subkey)
                    except Exception:
                        continue
                winreg.CloseKey(registry_key)
            except Exception:
                continue
        return installed_apps

    def scan_and_log_installed_apps(self) -> int:
        installed_apps = self.get_installed_apps()
        logged_count = 0
        for app in installed_apps:
            try:
                executable_path = app["install_location"]
                if not executable_path or executable_path == "Unknown":
                    executable_path = f"UNKNOWN::{app['name']}"
                if updateAppTable(
                    appName=app["name"],
                    executablePath=executable_path,
                    vendor=app["vendor"],
                ):
                    logged_count += 1
            except Exception as e:
                logging.debug(f"Failed to log app {app.get('name', 'Unknown')}: {e}")
        logging.info(f"Logged {logged_count}/{len(installed_apps)} installed apps")
        return logged_count

    def log_apps(self) -> int:
        return self.scan_and_log_installed_apps()

    def cleanup(self) -> None:
        if self.is_running:
            self.stop_monitoring()
