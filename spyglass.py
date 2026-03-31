"""
Spyglass Integrated Test
This module provides an integrated testing interface for both app monitoring and keylogging.
Users can choose between high security (app monitoring + keylogging) and low security (app monitoring only).
"""

import sys
import time
import logging
import datetime
import os
from typing import Dict, Any, Optional

from appMonitor import AppMonitor
from keystroke_monitor import KeystrokeMonitor
from database import DatabaseManager
from consent import ConsentScreen
from adminHandler import AdminHandler
from keylogger import Keylogger
from configSettings import create_config, ConfigSettings
from userInfo import UserInfo
from alert_manager import AlertManager
from threshold_engine import ThresholdEngine


class Spyglass:
    def __init__(self):
        self.app_monitor: Optional[AppMonitor] = None
        self.keystroke_monitor: Optional[KeystrokeMonitor] = None
        self.consent = None
        self.config: Optional[ConfigSettings] = None
        self.database: Optional[DatabaseManager] = None
        self.keylogger = None
        self.monitoring_level = None
        self.is_running = False
        self.alert_manager: Optional[AlertManager] = None
        self.threshold_engine: Optional[ThresholdEngine] = None
        self.thresholds: Dict[str, Dict[str, Any]] = {}

    def run(self) -> bool:
        print("\n" + "=" * 70)
        print("WELCOME TO SPYGLASS".center(70))
        print("=" * 70 + "\n")

        logging.info("Initializing...")
        logging.info("Starting APP setup - Checking admin privileges...")
        if not self.verify_admin():
            logging.error("Administrator privileges verification failed.")
            return False
        logging.info("Administrator privileges verified")

        logging.info("Getting User consent...")
        if not self.get_consent():
            logging.error("User did not provide consent. Exiting.")
            return False
        logging.info("User consent obtained")

        logging.info("Setting up configuration...")
        if not self.setup_config():
            logging.error("Configuration setup failed. Exiting.")
            return False
        logging.info("Configuration setup complete")

        logging.info("Setting up database...")
        if not self.setup_db():
            logging.error("Database setup failed. Exiting.")
            return False
        logging.info("Database setup initialized successfully")

        self.monitoring_level = self.consent.get_monitoring_level()
        self.threshold_engine = ThresholdEngine(self.monitoring_level)
        self.thresholds = self.threshold_engine.get_thresholds()

        self.alert_manager = AlertManager(
            database=self.database,
            monitoring_level=self.monitoring_level,
            cooldown_seconds=self.thresholds["alerting"]["cooldown_seconds"],
            startup_grace_seconds=self.thresholds["alerting"]["startup_grace_seconds"],
        )

        self.keylogger = Keylogger(self)
        self.app_monitor = AppMonitor(
            poll_interval=self.thresholds["application"]["poll_interval_seconds"],
            monitoring_level=self.monitoring_level,
            alert_manager=self.alert_manager,
        )

        app_count = self.app_monitor.scan_and_log_installed_apps()
        logging.info(f"Installed apps logged to DB: {app_count}")
        self.is_running = True

        if self.config.is_keylogger_enabled():
            print("\nKeystroke logging is ENABLED")
            logging.info("Keystroke logging is ENABLED")
            self.keystroke_monitor = KeystrokeMonitor(
                alert_manager=self.alert_manager,
                monitoring_level=self.monitoring_level,
            )
        else:
            print("\nKeystroke logging is DISABLED")
            logging.info("Keystroke logging is DISABLED")

        print("\n" + "=" * 70)
        print("SPYGLASS INITIALIZATION COMPLETE".center(70))
        print("=" * 70 + "\n")
        return True

    def verify_admin(self) -> bool:
        try:
            logging.info("Checking admin privileges...")
            AdminHandler.check_and_request_admin()
            print("Current privilege level: Admin")
            print("Administrator privileges confirmed.\n")
            logging.info("Administrator privileges confirmed")
            return True
        except Exception as e:
            print(f"Error checking admin privileges: {e}\n")
            logging.error(f"Error checking admin privileges: {e}", exc_info=True)
            return False

    def get_consent(self) -> bool:
        try:
            print("User Consent & Monitoring Level Selection...\n")
            logging.info("Creating ConsentScreen...")
            self.consent = ConsentScreen()
            logging.info("Displaying consent screen...")
            if not self.consent.display_consent():
                print("\nConsent was not given. Test cannot continue.\n")
                logging.warning("User declined consent")
                return False

            self.monitoring_level = self.consent.get_monitoring_level()
            print(f"\nConsent received. Monitoring level: {self.monitoring_level}\n")
            logging.info(f"Consent received with monitoring level: {self.monitoring_level}")
            return True
        except Exception as e:
            print(f"\nError during consent: {e}\n")
            logging.error(f"Error during consent: {e}", exc_info=True)
            return False

    def setup_config(self) -> bool:
        try:
            print("Configuring Monitoring Settings...\n")
            logging.info(f"Creating config with monitoring level: {self.monitoring_level}")
            self.config = create_config(self.monitoring_level)
            self.config.print_settings()
            return True
        except Exception as e:
            print(f"\nError setting up config: {e}\n")
            logging.error(f"Error setting up config: {e}", exc_info=True)
            return False

    def setup_db(self) -> bool:
        try:
            print("Initializing Encrypted Database...\n")
            import hashlib

            encryption_key = hashlib.sha256(b"spyglass_secure_key_v1").hexdigest()
            self.database = DatabaseManager()
            self.database.initializeDB(create_tables=True, encryption_key=encryption_key)

            user_info = UserInfo()
            device_info = user_info.to_dict()
            system_info_path = os.path.join(os.path.dirname(__file__), "system_info.json")
            user_info.save_to_file(system_info_path)
            logging.info(f"System information saved to: {system_info_path}")

            self.database.UpdateUserTable(deviceInfo=device_info)

            if not self.database.verifyConnection():
                logging.error("Database connection verification failed")
                return False

            print("Database initialized successfully.\n")
            logging.info("Database setup complete")
            return True
        except Exception as e:
            print(f"\nError setting up database: {e}\n")
            logging.error(f"Error setting up database: {e}", exc_info=True)
            return False

    def start_app_monitoring(self, duration: int = 180) -> bool:
        if not self.is_running:
            print("Spyglass has not been initialized. Please run setup first.\n")
            return False

        print("\n" + "=" * 70)
        print("APP MONITORING TEST".center(70))
        print("=" * 70 + "\n")
        print(f"Starting app monitoring for {duration} seconds...")
        print("Switch between different applications. All app usage will be tracked.\n")
        logging.info(f"Starting app monitoring for {duration} seconds")

        try:
            if not self.app_monitor.start_monitoring():
                print("Failed to start app monitoring.\n")
                logging.error("Failed to start app monitoring")
                return False

            print("App monitoring started.")
            print(f"Monitoring will continue for {duration} seconds...\n")
            logging.info("App monitoring successfully started")

            for remaining in range(duration, 0, -1):
                sys.stdout.write(f"\r⏱  Remaining time: {remaining:3d} seconds")
                sys.stdout.flush()
                time.sleep(1)

            sys.stdout.write("\r" + " " * 50 + "\r")
            self.app_monitor.stop_monitoring()
            print("\nApp monitoring stopped.\n")
            logging.info("App monitoring stopped")
            return True

        except Exception as e:
            print(f"\nError during app monitoring: {e}\n")
            logging.error(f"Error during app monitoring: {e}", exc_info=True)
            return False

    def start_integrated_test(self, duration: int = 180) -> bool:
        return self.full_monitoring(duration)

    def full_monitoring(self, duration: int = 180) -> bool:
        if not self.is_running:
            print("Spyglass has not been initialized. Please run setup first.\n")
            return False

        if not self.config.is_keylogger_enabled():
            print("\nIntegrated test requires HIGH monitoring level.")
            print("Current level does not have keystroke monitoring enabled.\n")
            return False

        print("\n" + "=" * 70)
        print("INTEGRATED MONITORING TEST (HIGH SECURITY)".center(70))
        print("=" * 70 + "\n")
        print(f"Starting integrated monitoring for {duration} seconds...")
        print("Switch between apps and type freely. Alerts will appear only for threshold violations.\n")
        logging.info(f"Starting integrated monitoring for {duration} seconds")

        try:
            if not self.app_monitor.start_monitoring():
                print("Failed to start app monitoring.\n")
                return False

            if not self.keystroke_monitor.startLog():
                print("Failed to start keystroke monitoring.\n")
                self.app_monitor.stop_monitoring()
                return False

            print("Integrated monitoring started (App + Keystroke).")
            print(f"Monitoring will continue for {duration} seconds...\n")
            logging.info("Integrated monitoring started successfully")

            for remaining in range(duration, 0, -1):
                sys.stdout.write(f"\r⏱  Remaining time: {remaining:3d} seconds")
                sys.stdout.flush()
                time.sleep(1)

            sys.stdout.write("\r" + " " * 50 + "\r")
            self.app_monitor.stop_monitoring()
            self.keystroke_monitor.stopLog()

            print("\nIntegrated monitoring stopped.\n")
            self.display_keystroke_results()
            return True

        except Exception as e:
            print(f"\nError during integrated monitoring: {e}\n")
            logging.error(f"Error during integrated monitoring: {e}", exc_info=True)
            return False

    def display_keystroke_results(self) -> None:
        if not self.keystroke_monitor:
            return

        with self.keystroke_monitor.lock:
            keylogger_data = dict(self.keystroke_monitor.keystrokes)

        if not keylogger_data:
            print("\nNo keystrokes were captured during this session.\n")
            logging.warning("No keystrokes captured")
            return

        print("\n" + "=" * 70)
        print("KEYSTROKE CAPTURE RESULTS".center(70))
        print("=" * 70 + "\n")

        total_keys = sum(keylogger_data.values())
        print(f"Total Keystrokes Captured: {total_keys}")
        print(f"Unique Keys Pressed: {len(keylogger_data)}\n")
        print("Top 10 Most Pressed Keys:")
        print("-" * 50)

        for key, count in sorted(keylogger_data.items(), key=lambda x: x[1], reverse=True)[:10]:
            key_display = key
            if key == "Key.space":
                key_display = "[SPACE]"
            elif key == "Key.enter":
                key_display = "[ENTER]"
            elif key == "Key.backspace":
                key_display = "[BACKSPACE]"
            elif key == "Key.tab":
                key_display = "[TAB]"
            elif len(key) > 1 and key.startswith("Key."):
                key_display = f"[{key.replace('Key.', '').upper()}]"
            else:
                key_display = f"'{key}'"

            bar_length = int(count / max(keylogger_data.values()) * 40)
            print(f"  {key_display:20s} {count:4d} {'=' * bar_length}")

        print("\n" + "=" * 70 + "\n")

    def show_current_settings(self) -> None:
        if self.config:
            self.config.print_settings()
        if self.threshold_engine:
            print("ALERT THRESHOLDS")
            print("-" * 60)
            for section, values in self.thresholds.items():
                print(f"\n[{section.upper()}]")
                for key, value in values.items():
                    print(f"  {key}: {value}")
            print("\n" + "=" * 60 + "\n")

    def show_running_apps(self) -> None:
        running_apps = self.app_monitor.get_running_apps() if self.app_monitor else []
        if not running_apps:
            print("\nNo running applications found.\n")
            return

        print("\n" + "=" * 90)
        print("RUNNING APPLICATIONS".center(90))
        print("=" * 90)
        print(f"{'Application Name':<30} {'PID':<8} {'Memory (MB)':<12} {'CPU %':<8} {'Window Title':<28}")
        print("-" * 90)

        for app in sorted(running_apps, key=lambda x: x["memory_mb"], reverse=True):
            name = app["name"][:28] if len(app["name"]) > 28 else app["name"]
            pid = str(app["pid"])
            memory = f"{app['memory_mb']:.1f}"
            cpu = f"{app['cpu_percent']:.1f}"
            title = app["window_title"][:26] if len(app["window_title"]) > 26 else app["window_title"]
            print(f"{name:<30} {pid:<8} {memory:<12} {cpu:<8} {title:<28}")

        print("\n" + "=" * 90 + "\n")

    def show_menu(self) -> None:
        while True:
            print("=" * 70)
            print("SPYGLASS TEST MENU".center(70))
            print("=" * 70)
            print(f"Monitoring Level: {self.monitoring_level}")
            print(f"Keystroke Logging: {'ENABLED' if self.config and self.config.is_keylogger_enabled() else 'DISABLED'}")
            print("\n1. Start App Monitoring Test (180 seconds)")
            if self.config and self.config.is_keylogger_enabled():
                print("2. Start Integrated Test - HIGH SECURITY (180 seconds)")
            else:
                print("2. Start Integrated Test - HIGH SECURITY (Unavailable in LOW)")
            print("3. Show Current Settings")
            print("4. Show Running Apps Snapshot")
            print("5. Exit")
            choice = input("\nEnter your choice (1-5): ").strip()

            if choice == "1":
                self.start_app_monitoring(180)
            elif choice == "2":
                if self.config and self.config.is_keylogger_enabled():
                    self.start_integrated_test(180)
                else:
                    print("\nIntegrated test is only available in HIGH monitoring mode.\n")
            elif choice == "3":
                self.show_current_settings()
            elif choice == "4":
                self.show_running_apps()
            elif choice == "5":
                print("\nExiting Spyglass.\n")
                break
            else:
                print("\nInvalid choice. Please enter 1-5.\n")

    def cleanup(self) -> None:
        if self.database:
            self.database.closeDB()
        if self.app_monitor:
            self.app_monitor.cleanup()
        if self.keystroke_monitor and self.keystroke_monitor.listener:
            self.keystroke_monitor.stopLog()


def main():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    reports_dir = os.path.join(os.path.dirname(__file__), "Reports")
    os.makedirs(reports_dir, exist_ok=True)
    log_file = os.path.join(reports_dir, f"spyglass_test_{timestamp}.log")
    keystroke_log_file = os.path.join(reports_dir, f"keystrokes_{timestamp}.log")

    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG)

    keystroke_logger = logging.getLogger("keystrokes")
    keystroke_logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    app_file_handler = logging.FileHandler(log_file, encoding="utf-8")
    app_file_handler.setFormatter(formatter)
    app_logger.addHandler(app_file_handler)

    app_console_handler = logging.StreamHandler()
    app_console_handler.setFormatter(formatter)
    app_logger.addHandler(app_console_handler)

    keystroke_file_handler = logging.FileHandler(keystroke_log_file, encoding="utf-8")
    keystroke_file_handler.setFormatter(formatter)
    keystroke_logger.addHandler(keystroke_file_handler)

    logging.root.handlers = []
    logging.root.addHandler(app_file_handler)
    logging.root.addHandler(app_console_handler)
    logging.root.setLevel(logging.DEBUG)

    logging.info("=" * 70)
    logging.info("SPYGLASS TEST STARTED")
    logging.info("=" * 70)
    logging.info(f"Application log: {log_file}")
    logging.info(f"Keystroke log: {keystroke_log_file}")

    app = None
    try:
        logging.info("Initializing Spyglass test...")
        app = Spyglass()
        logging.info("Running Spyglass setup...")
        if app.run():
            logging.info("Setup completed successfully. Showing a menu...")
            app.show_menu()
        else:
            logging.warning("Setup did not complete successfully.")
        logging.info("Cleaning up resources...")
    except KeyboardInterrupt:
        logging.info("Spyglass interrupted by user.")
        print("\n\nSpyglass interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if app is not None:
            app.cleanup()
        logging.info("Spyglass shutdown completed.")


if __name__ == "__main__":
    main()
