"""Welcome to Spyglass"""
import sys
import time
import logging
import datetime
import os
from typing import Dict, Any, Optional

from appMonitor import AppMonitor
from keystroke_monitor import KeystrokeMonitor
from database import DatabaseManager, insertIntoKeystrokeSummaryTable
from consent import ConsentScreen
from adminHandler import AdminHandler
from keylogger import Keylogger
from alertEngine import AlertEngine
from configSettings import create_config, ConfigSettings
from userInfo import UserInfo

class Spyglass:
    def __init__(self):
        self.app_monitor: Optional[AppMonitor] = None
        self.consent = None
        self.config = None
        self.database = None
        self.user_info: Optional[UserInfo] = None
        self.keylogger = None
        self.alert_engine: Optional[AlertEngine] = None
        self.monitoring_level = None
        self.monitoring_active = False
        self.is_running = False
    
    def run(self) -> bool:
        #Run the complete Spyglass a setup
        print("\n" + "="*70)
        print("WELCOME TO SPYGLASS".center(70))
        print("="*70 + "\n")
        
        # STARTING SPYGLASS
        logging.info("Initializing...")
        logging.info("Starting APP setup - Checking admin privileges...")
        if not self.verify_admin():
            logging.error("Administrator privileges verification failed.")
            return False   
        logging.info("Administrator privileges verified")
        
        #Consent Screen
        logging.info("Getting User consent...")
        if not self.get_consent():
            logging.error("User did not provide consent. Exiting.")
            return False
        logging.info("User consent obtained")
        
        #Setup Config
        logging.info("Setting up configuration...")
        if not self.setup_config():
            logging.error("Configuration setup failed. Exiting.")
            return False
        logging.info("Configuration setup complete")
        
        # DB Initialization
        logging.info("Setting up database...")
        if not self.setup_db():
            logging.error("Database setup failed. Exiting.")
            return False
        logging.info("Database setup initialized successfully")
        

        # system setup
        self.keylogger = Keylogger(self)
        self.app_monitor = AppMonitor()
        self.monitoring_level = self.consent.get_monitoring_level()

        # Log installed apps to DB
        app_count = self.app_monitor.scan_and_log_installed_apps()
        logging.info(f"Installed apps logged to DB: {app_count}")
        self.is_running = True

        # Create alert engine
        user_id = self.user_info.info.get('hardware', {}).get('machine_id', '') if self.user_info else ''
        self.alert_engine = AlertEngine(user_id)
        
        # Check if keylogging is enabled
        if self.config.is_keylogger_enabled():
            print("\nKeystroke logging is ENABLED (HIGH monitoring level)")
            logging.info("Keystroke logging is ENABLED")
        else:
            print("\nKeystroke logging is DISABLED (LOW monitoring level)")
            logging.info("Keystroke logging is DISABLED")
        
        print("\n" + "="*70)
        print("SPYGLASS INITIALIZATION COMPLETE".center(70))
        print("="*70 + "\n")
        
        return True
    
    def verify_admin(self) -> bool:
        # Check and request admin privileges
        try:
            logging.info("Checking admin privileges...")
            # Request admin if not already running as admin
            AdminHandler.check_and_request_admin()
            
            # If we get here, we're running as admin
            print(f"Current privilege level: Admin")
            print("Administrator privileges confirmed.\n")
            logging.info("Administrator privileges confirmed")
            return True
        except Exception as e:
            print(f"Error checking admin privileges: {e}\n")
            logging.error(f"Error checking admin privileges: {e}", exc_info=True)
            return False
    
    def get_consent(self) -> bool:
        # Display consent screen and get user consent# 
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
        # Create and setup configuration from consent# 
        try:
            print("Configuring Monitoring Settings...\n")
            logging.info(f"Creating config with monitoring level: {self.monitoring_level}")
            self.config = create_config(self.monitoring_level)
            logging.info("Config created successfully")
            logging.info("Printing config settings...")
            self.config.print_settings()
            logging.info("Config settings printed")
            return True
        except Exception as e:
            print(f"\nError setting up config: {e}\n")
            logging.error(f"Error setting up config: {e}", exc_info=True)
            return False
    
    def setup_db(self) -> bool:
        # Initialize the database# 
        try:
            print("Initializing Encrypted Database...\n")
            logging.info("Creating DatabaseManager...")
            import hashlib
            encryption_key = hashlib.sha256(b"spyglass_secure_key_v1").hexdigest()
            
            self.database = DatabaseManager()
            logging.info("Initializing database...")
            self.database.initializeDB(create_tables=True, encryption_key=encryption_key)
            
            user_info = UserInfo()
            device_info = user_info.to_dict()
            system_info_path = os.path.join(os.path.dirname(__file__), 'system_info.json')
            user_info.save_to_file(system_info_path)
            logging.info(f"System information saved to: {system_info_path}")

            self.database.insertIntoUserTable(deviceInfo=device_info)
            self.user_info = user_info
            
            logging.info("Verifying database connection...")
            if not self.database.verifyConnection():
                logging.error("Database connection verification failed")
                return False
            
            print("Database initialized with SQLCipher encryption and verified.\n")
            logging.info("Database setup complete")
            return True
        except Exception as e:
            print(f"\nError setting up database: {e}\n")
            logging.error(f"Error setting up database: {e}", exc_info=True)
            return False
        
    def start_all_monitoring(self) -> None:
        #Start app monitoring, alert engine, and keystroke logging (if HIGH)
        print("\nStarting monitoring...")
        logging.info("Starting System monitoring...")
        self.app_monitor.start_monitoring()
        if self.config.is_keylogger_enabled():
            self.keylogger.start_keylogger()
        if self.alert_engine:
            self.alert_engine.start()
        self.monitoring_active = True
        print("Monitoring is now ACTIVE.\n")
        logging.info("System monitoring started")

    def stop_all_monitoring(self) -> None:
        #Stop all active monitoring
        print("\nStopping monitoring...")
        logging.info("Stopping System monitoring...")
        self.app_monitor.stop_monitoring()
        if self.config.is_keylogger_enabled():
            self.keylogger.stop_keylogger()
        if self.alert_engine:
            self.alert_engine.stop()
        self.monitoring_active = False
        print("Monitoring stopped.\n")
        logging.info("System monitoring stopped")

    def show_reports(self) -> None:
        #List report files in Reports directory
        print("\n" + "=" * 70)
        print("SPYGLASS REPORTS".center(70))
        print("=" * 70 + "\n")
        reports_dir = os.path.join(os.path.dirname(__file__), 'Reports')
        if not os.path.isdir(reports_dir):
            print("No reports directory found.\n")
            return
        files = sorted(os.listdir(reports_dir))
        if not files:
            print("No reports available.\n")
            return
        for i, f in enumerate(files, 1):
            print(f"  {i}. {f}")
        print(f"\nTotal: {len(files)} report(s)\n")
        print("=" * 70 + "\n")

    def show_menu(self) -> None:
        #Unified menu for LOW and HIGH monitoring
        while True:
            print("=" * 70)
            display_name = "User"
            if self.user_info and isinstance(self.user_info.info, dict):
                sys_info = self.user_info.info.get('system', {})
                hw_info = self.user_info.info.get('hardware', {})
                username = sys_info.get('username')
                hostname = sys_info.get('hostname')
                machine_id = hw_info.get('machine_id')

                if isinstance(username, str) and username.strip():
                    display_name = username.upper()
                elif isinstance(hostname, str) and hostname.strip():
                    display_name = hostname.upper()
                elif isinstance(machine_id, str) and machine_id.strip():
                    display_name = machine_id
            print(f"WELCOME {display_name}".ljust(70))
            print("=" * 70)

            level = self.monitoring_level or "LOW"
            mode = "HIGH (App Monitoring + Keystroke Logging)" if self.config.is_keylogger_enabled() else "LOW (App Monitoring Only)"
            status = "ACTIVE" if self.monitoring_active else "INACTIVE"
            print(f"\nMonitoring Level: {level}")
            print(f"Security Mode: {mode}")
            print(f"Monitoring Status: {status}\n")

            toggle_label = "Stop Monitoring" if self.monitoring_active else "Start Monitoring"
            print(f"1. {toggle_label}")
            print("2. Show Current Settings")
            print("3. View Installed Apps")
            print("4. View Running Apps")
            print("5. Show Reports")
            print("6. Exit\n")

            choice = input("Select option (1-6): ").strip().lower()

            if choice in ('1', 'stop') and self.monitoring_active:
                self.stop_all_monitoring()
            elif choice == '1':
                self.start_all_monitoring()
            elif choice == '2':
                self.config.print_settings()
            elif choice == '3':
                self.show_installed_apps()
            elif choice == '4':
                self.show_running_apps()
            elif choice == '5':
                self.show_reports()
            elif choice in ('6','stop'):
                if self.monitoring_active:
                    self.stop_all_monitoring()
                print("\nExiting Spyglass...\n")
                break
            else:
                print("\nInvalid choice. Please select between 1-6.\n")
    
    def show_installed_apps(self) -> None:
        """Display applications logged in the database"""
        print("\n" + "="*70)
        print("SPYGLASS - MY APPS".center(70))
        print("="*70 + "\n")

        if not self.database or not self.database.connection:
            print("Database is not available.\n")
            return

        try:
            cursor = self.database.connection.cursor()
            cursor.execute(
                """
                SELECT appName, vendor, executablePath
                FROM application
                ORDER BY appName COLLATE NOCASE ASC
                """
            )
            logged_apps = cursor.fetchall()
            cursor.close()
        except Exception as e:
            print(f"Error reading applications from database: {e}\n")
            logging.error(f"Error reading applications from database: {e}", exc_info=True)
            return

        if not logged_apps:
            print("No applications have been logged to the database yet.\n")
            return

        print(f"Found {len(logged_apps)} applications logged in the database:\n")
        print(f"{'Application Name':<30} {'Vendor':<22} {'Executable Path':<35}")
        print("-" * 90)

        for app_name, vendor, executable_path in logged_apps[:50]:
            display_name = app_name[:28] if len(app_name) > 28 else app_name
            display_vendor = (vendor or 'Unknown')[:20] if vendor else 'Unknown'
            display_path = executable_path[:33] if len(executable_path) > 33 else executable_path
            print(f"{display_name:<30} {display_vendor:<22} {display_path:<35}")

        if len(logged_apps) > 50:
            print(f"\n... and {len(logged_apps) - 50} more applications")
        
        print("\n" + "="*70 + "\n")
    
    def show_running_apps(self) -> None:
        """Display all currently running applications"""
        print("\n" + "="*70)
        print("SPYGLASS - RUNNING APPLICATIONS".center(70))
        print("="*70 + "\n")
        
        print("Scanning for running applications...\n")
        running_apps = self.app_monitor.get_running_apps()
        
        if not running_apps:
            print("No running applications found.\n")
            return
        
        print(f"Found {len(running_apps)} running applications:\n")
        print(f"{'Application Name':<30} {'PID':<8} {'Memory (MB)':<12} {'CPU %':<8} {'Window Title':<30}")
        print("-" * 90)
        
        for app in sorted(running_apps, key=lambda x: x['memory_mb'], reverse=True):
            name = app['name'][:28] if len(app['name']) > 28 else app['name']
            pid = str(app['pid'])
            memory = f"{app['memory_mb']:.1f}"
            cpu = f"{app['cpu_percent']:.1f}"
            title = app['window_title'][:28] if len(app['window_title']) > 28 else app['window_title']
            print(f"{name:<30} {pid:<8} {memory:<12} {cpu:<8} {title:<30}")
        
        print("\n" + "="*70 + "\n")
    
    def cleanup(self) -> None:
        """Clean up resources"""
        if self.monitoring_active:
            self.stop_all_monitoring()
        if self.database:
            self.database.closeDB()
        if self.app_monitor:
            self.app_monitor.cleanup()


def main():
    # App Entry Point
    """Main entry point for the Spyglass test """
    # Setup file logging with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    reports_dir = os.path.join(os.path.dirname(__file__), 'Reports')
   
    # make the folder if it doesn't exist
    os.makedirs(reports_dir, exist_ok=True)
    log_file = os.path.join(reports_dir, f'spyglass_{timestamp}.log')
    keystroke_log_file = os.path.join(reports_dir, f'keystrokes_{timestamp}.log')
    
    # Create separate loggers for application activity and keystroke data
    app_logger = logging.getLogger('app')
    app_logger.setLevel(logging.DEBUG)
    
    keystroke_logger = logging.getLogger('keystrokes')
    keystroke_logger.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # App logger handlers (application activity)
    app_file_handler = logging.FileHandler(log_file, encoding='utf-8')
    app_file_handler.setFormatter(formatter)
    app_logger.addHandler(app_file_handler)
    
    app_console_handler = logging.StreamHandler()
    app_console_handler.setFormatter(formatter)
    app_logger.addHandler(app_console_handler)
    
    # Keystroke logger handlers (keystroke data only)
    keystroke_file_handler = logging.FileHandler(keystroke_log_file, encoding='utf-8')
    keystroke_file_handler.setFormatter(formatter)
    keystroke_logger.addHandler(keystroke_file_handler)
    
    # Set root logger to use app logger handlers
    logging.root.handlers = []
    logging.root.addHandler(app_file_handler)
    logging.root.addHandler(app_console_handler)
    logging.root.setLevel(logging.DEBUG)
    
    logging.info("=" * 70)
    logging.info("SPYGLASS TEST STARTED")
    logging.info("=" * 70)
    logging.info(f"Application log: {log_file}")
    logging.info(f"Keystroke log: {keystroke_log_file}")
    
    try:
        logging.info("Initializing Spyglass test...")
        app = Spyglass()
        logging.info("Running Spyglass setup...")
        if app.run():
            logging.info("Setup completed successfully. Showing a menu...")
            try:
                app.show_menu()
            except Exception as menu_error:
                logging.error(f"Error in show_menu: {menu_error}", exc_info=True)
                print(f"\nError displaying menu: {menu_error}")
                raise
        else:
            logging.warning("Setup did not complete successfully.")
        logging.info("Cleaning up resources...")
        app.cleanup()
        logging.info("Spyglass shutdown completed.")
        
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


if __name__ == "__main__":
    main()