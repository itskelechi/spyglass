import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
import sys
import psutil
import winreg

from database import updateAppTable


class AppMonitor:
    def __init__(self, poll_interval: float = 15.0):
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.current_process: Optional[Dict[str, Any]] = None
        self.last_update: Optional[datetime] = None
        self.poll_interval = poll_interval

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
                    logging.info(
                        f"Active app changed: {foreground['name']} | {foreground['window_title']}"
                    )

                threading.Event().wait(self.poll_interval)
            except Exception as e:
                logging.error(f"Error in app monitor loop: {e}")

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
            for process in psutil.process_iter([
                "pid",
                "name",
                "exe",
                "status",
                "memory_info",
                "cpu_percent",
            ]):
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

    def cleanup(self) -> None:
        if self.is_running:
            self.stop_monitoring()
