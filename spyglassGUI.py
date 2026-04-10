"""Spyglass GUI Application Entry Point.

Orchestrates: Admin check → Consent window → Threshold config → Setup → Dashboard.
"""

import sys
import os
import logging
import datetime
import hashlib

from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QIcon

from gui.styles import GLOBAL_STYLESHEET, COLORS
from gui.consent_window import ConsentWindow
from gui.threshold_window import ThresholdWindow
from gui.dashboard import DashboardWindow

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from spyglass import Spyglass
from config.adminHandler import AdminHandler
from config.configSettings import create_config
from db.database import DatabaseManager
from userInfo import UserInfo
from monitoring.keylogger import Keylogger
from monitoring.appMonitor import AppMonitor
from alertEngine import AlertEngine
from config.consent import ConsentScreen


class SetupThread(QThread):
    """Run config + DB setup off the main thread."""
    step_done = pyqtSignal(str, bool)   # step_name, success
    finished_setup = pyqtSignal(bool)   # overall ok
    error = pyqtSignal(str)

    def __init__(self, spyglass):
        super().__init__()
        self.spyglass = spyglass

    def run(self):
        # Config
        try:
            ok = self.spyglass.setup_config()
            self.step_done.emit("config", ok)
            if not ok:
                self.finished_setup.emit(False)
                return
        except Exception as e:
            self.error.emit(f"Config error: {e}")
            self.finished_setup.emit(False)
            return

        # Database
        try:
            ok = self.spyglass.setup_db()
            self.step_done.emit("database", ok)
            if not ok:
                self.finished_setup.emit(False)
                return
        except Exception as e:
            self.error.emit(f"Database error: {e}")
            self.finished_setup.emit(False)
            return

        self.finished_setup.emit(True)


def _setup_logging() -> str:
    """Configure file + console logging identical to main.py."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    reports_dir = os.path.join(os.path.dirname(__file__), "Reports")
    os.makedirs(reports_dir, exist_ok=True)
    log_file = os.path.join(reports_dir, f"spyglass_{timestamp}.log")

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(formatter)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    logging.root.handlers = []
    logging.root.addHandler(fh)
    logging.root.addHandler(ch)
    logging.root.setLevel(logging.DEBUG)

    return log_file


def run_gui():
    """Launch the Spyglass GUI application."""
    log_file = _setup_logging()
    logging.info("=" * 70)
    logging.info("SPYGLASS GUI STARTED")
    logging.info("=" * 70)
    logging.info(f"Log file: {log_file}")

    app = QApplication(sys.argv)
    app.setApplicationName("Spyglass")
    _logo = os.path.join(os.path.dirname(__file__), "logo", "spyglass_logo.png")
    if os.path.isfile(_logo):
        app.setWindowIcon(QIcon(_logo))
    app.setStyleSheet(GLOBAL_STYLESHEET)

    # ── 1. Admin Check ───────────────────────────────────────────────
    logging.info("Checking admin privileges...")
    try:
        AdminHandler.check_and_request_admin()
        logging.info("Admin privileges confirmed.")
    except Exception as e:
        QMessageBox.critical(None, "Spyglass", f"Administrator privileges required.\n\n{e}")
        sys.exit(1)

    # ── 2. Consent Window ────────────────────────────────────────────
    logging.info("Showing consent window...")
    consent_dialog = ConsentWindow()
    result = consent_dialog.exec()
    if not result:
        logging.warning("User declined consent.")
        QMessageBox.information(None, "Spyglass", "Consent declined. Exiting.")
        sys.exit(0)

    monitoring_level = consent_dialog.get_selected_level()
    logging.info(f"Consent given. Monitoring level: {monitoring_level}")

    # ── 3. Threshold Configuration ───────────────────────────────────
    logging.info("Showing threshold configuration...")
    threshold_dialog = ThresholdWindow(monitoring_level=monitoring_level)
    threshold_dialog.exec()
    user_thresholds = threshold_dialog.get_thresholds()
    logging.info(f"Thresholds configured: {user_thresholds}")

    # ── 4. Build Spyglass Core Object ────────────────────────────────
    spy = Spyglass()
    spy.monitoring_level = monitoring_level

    # Create a ConsentScreen-compatible object so existing code works
    consent_obj = ConsentScreen()
    consent_obj.user_consented = True
    consent_obj.monitoring_level = monitoring_level
    consent_obj.thresholds = user_thresholds
    spy.consent = consent_obj

    # Setup config
    logging.info("Setting up configuration...")
    spy.config = create_config(monitoring_level)
    spy.config.set_setting("thresholds", user_thresholds)
    spy.config.save_config()
    logging.info("Config created.")

    # Setup database
    logging.info("Setting up database...")
    try:
        encryption_key = hashlib.sha256(b"spyglass_secure_key_v1").hexdigest()
        spy.database = DatabaseManager()
        spy.database.initializeDB(create_tables=True, encryption_key=encryption_key)
        from db.database import setDB
        setDB(spy.database)

        user_info = UserInfo()
        device_info = user_info.to_dict()
        system_info_path = os.path.join(os.path.dirname(__file__), "system_info.json")
        user_info.save_to_file(system_info_path)
        spy.database.insertIntoUserTable(deviceInfo=device_info)
        spy.user_info = user_info

        # Persist thresholds to DB
        machine_id = user_info.info.get("hardware", {}).get("machine_id", "")
        from db.database import insertIntoThresholdTable
        for setting_name, severity_dict in user_thresholds.items():
            for severity, value in severity_dict.items():
                insertIntoThresholdTable(
                    userID=machine_id,
                    thresholdType="security",
                    settingName=f"{setting_name}_{severity}",
                    settingValue=str(value),
                )

        if not spy.database.verifyConnection():
            raise RuntimeError("Database verification failed")
        logging.info("Database setup complete.")
    except Exception as e:
        logging.error(f"Database setup failed: {e}", exc_info=True)
        QMessageBox.critical(None, "Spyglass", f"Database setup failed:\n\n{e}")
        sys.exit(1)

    # Initialise subsystems
    spy.keylogger = Keylogger(spy)
    spy.app_monitor = AppMonitor()
    app_count = spy.app_monitor.scan_and_log_installed_apps()
    logging.info(f"Installed apps logged: {app_count}")
    spy.is_running = True

    user_id = spy.user_info.info.get("hardware", {}).get("machine_id", "") if spy.user_info else ""
    spy.alert_engine = AlertEngine(user_id, user_thresholds=user_thresholds)

    # ── 5. Show Dashboard ────────────────────────────────────────────
    logging.info("Launching dashboard...")
    dashboard = DashboardWindow(spy)
    dashboard.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
