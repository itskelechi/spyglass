"""Welcome to Spyglass"""
import sys
import time
import logging
import datetime
import os
from typing import Dict, Any, Optional

from appMonitor import AppMonitor
from keystroke_monitor import KeystrokeMonitor
from database import DatabaseManager, updateKeystrokeSummaryTable
from consent import ConsentScreen
from adminHandler import AdminHandler
from keylogger import Keylogger
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
        self.monitoring_level = None
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
        app_count = self.app_monitor.log_apps()
        logging.info(f"Installed apps logged to DB: {app_count}")
        self.is_running = True
        
        # Check if keylogging is enabled
        if self.config.is_keylogger_enabled():
            print("\nKeystroke logging is ENABLED (HIGH monitoring level)")
            logging.info("Keystroke logging is ENABLED")
            
            # Initialize keystroke monitor if high security
            self.keystroke_monitor = KeystrokeMonitor()
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

            self.database.UpdateUserTable(deviceInfo=device_info)
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
        
    def start_app_monitoring(self, duration: int = 180) -> bool:
        #Start application monitoring for specified duration
        if not self.is_running:
            print("Spyglass has not been initialized. Please run setup first.\n")
            return False
        
        print("\n" + "="*70)
        print("APP MONITORING TEST".center(70))
        print("="*70 + "\n")
        
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
            
            # Monitor for specified duration
            for remaining in range(duration, 0, -1):
                sys.stdout.write(f"\r⏱  Remaining time: {remaining:2d} seconds")
                sys.stdout.flush()
                time.sleep(1)
            
            sys.stdout.write("\r" + " " * 40 + "\r")  # Clear the line
            
            self.app_monitor.stop_monitoring()
            print("\nApp monitoring stopped.\n")
            logging.info("App monitoring stopped")
            return True
            
        except Exception as e:
            print(f"\nError during app monitoring: {e}\n")
            logging.error(f"Error during app monitoring: {e}", exc_info=True)
            return False
    
    def start_keylogger(self, duration: int = 180) -> bool:
        """Start keystroke logging for specified duration"""
        if not self.is_running:
            print("Spyglass has not been initialized. Please run setup first.\n")
            return False
        return self.keylogger.start_keylogger(duration)
    
    def full_monitoring(self, duration: int = 180) -> bool:
        #Start both app monitoring and keylogging together (HIGH security only)
        if not self.is_running:
            print("Spyglass has not been initialized. Please run setup first.\n")
            return False
        
        if not self.config.is_keylogger_enabled():
            print("\nIntegrated test requires HIGH monitoring level.")
            print("Current level: LOW (app monitoring only)\n")
            return False
        
        print("\n" + "="*70)
        print("INTEGRATED MONITORING TEST (HIGH SECURITY)".center(70))
        print("="*70 + "\n")
        
        print(f"Starting integrated monitoring for {duration} seconds...")
        print("Switch between apps and type freely. All activity will be tracked.\n")
        logging.info(f"Starting integrated monitoring for {duration} seconds")
        
        try:
            # Start app monitoring
            if not self.app_monitor.start_monitoring():
                print("Failed to start app monitoring.\n")
                return False
            
            # Start keystroke logging
            if not self.keystroke_monitor.startLog():
                print("Failed to start keystroke monitoring.\n")
                self.app_monitor.stop_monitoring()
                return False
            
            print("Integrated monitoring started (App + Keystroke).")
            print(f"Monitoring will continue for {duration} seconds...\n")
            logging.info("Integrated monitoring started successfully")
            
            # Monitor for specified duration
            for remaining in range(duration, 0, -1):
                sys.stdout.write(f"\r⏱  Remaining time: {remaining:2d} seconds")
                sys.stdout.flush()
                time.sleep(1)
            
            sys.stdout.write("\r" + " " * 40 + "\r")  # Clear the line
            
            # Save keystrokes before stopLog clears them
            with self.keystroke_monitor.lock:
                self.last_integrated_keystrokes = self.keystroke_monitor.keystrokes.copy()
            
            # Stop both monitors
            self.app_monitor.stop_monitoring()
            self.keystroke_monitor.stopLog()
            
            print("\nIntegrated monitoring stopped.\n")
            
            # Display results
            self.display_keystroke_results()
            return True
            
        except Exception as e:
            print(f"\nError during integrated monitoring: {e}\n")
            logging.error(f"Error during integrated monitoring: {e}", exc_info=True)
            return False
    
    def display_keystroke_results(self) -> None:
        """Display keystroke logging results"""
        if not self.keystroke_monitor:
            return
        
        keystroke_logger = logging.getLogger('keystrokes')
        
        with self.keystroke_monitor.lock:
            keylogger_data = self.keystroke_monitor.keystrokes.copy()
        
        if not keylogger_data and hasattr(self, 'last_integrated_keystrokes'):
            keylogger_data = self.last_integrated_keystrokes
        
        if not keylogger_data:
            print("\nNo keystrokes were captured during this session.\n")
            keystroke_logger.warning("No keystrokes captured")
            return
        
        print("\n" + "="*70)
        print("KEYSTROKE CAPTURE RESULTS".center(70))
        print("="*70 + "\n")
        
        total_keys = sum(keylogger_data.values())
        print(f"Total Keystrokes Captured: {total_keys}")
        print(f"Unique Keys Pressed: {len(keylogger_data)}\n")
        
        print("Top 10 Most Pressed Keys:")
        print("-" * 50)
        
        keystroke_logger.info("="*70)
        keystroke_logger.info("KEYSTROKE CAPTURE RESULTS")
        keystroke_logger.info("="*70)
        keystroke_logger.info(f"Total Keystrokes: {total_keys}")
        keystroke_logger.info(f"Unique Keys: {len(keylogger_data)}")
        keystroke_logger.info("\nTop 10 Most Pressed Keys:")
        
        for key, count in sorted(keylogger_data.items(), key=lambda x: x[1], reverse=True)[:10]:
            # Format key for display
            key_display = key
            if key == 'Key.space':
                key_display = '[SPACE]'
            elif key == 'Key.enter':
                key_display = '[ENTER]'
            elif key == 'Key.backspace':
                key_display = '[BACKSPACE]'
            elif key == 'Key.tab':
                key_display = '[TAB]'
            elif len(key) > 1 and key.startswith('Key.'):
                key_display = f"[{key.replace('Key.', '').upper()}]"
            else:
                key_display = f"'{key}'"
            
            bar_length = int(count / max(keylogger_data.values()) * 40)
            bar = "=" * bar_length
            print(f"  {key_display:20s} {count:4d} {bar}")
            keystroke_logger.info(f"  {key_display:20s} {count:4d}")
        
        keystroke_logger.info("="*70)
        keystroke_logger.info(f"ALL CAPTURED KEYSTROKES ({len(keylogger_data)} unique keys):")
        keystroke_logger.info("="*70)
        for key, count in sorted(keylogger_data.items(), key=lambda x: x[1], reverse=True):
            keystroke_logger.info(f"  {key}: {count}")
        
        print("\n" + "="*70 + "\n")
    
    def show_menu(self) -> None:
        #test menu
        while True:
            print("="*70)
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
            print("="*70)
            print(f"\nMonitoring Level: {self.monitoring_level}")
            
            if self.config.is_keylogger_enabled():
                print(f"Security Mode: HIGH (App Monitoring + Keystroke Logging)\n")
                print("1. Start App Monitoring Test (180 seconds)")
                print("2. Start Keystroke Logging Test (180 seconds)")
                print("3. Start Integrated Test - HIGH SECURITY (180 seconds)")
                print("4. Show Current Settings")
                print("5. View Installed Apps")
                print("6. View Running Apps")
                print("7. Exit Test\n")
                
                choice = input("Select option (1-7): ").strip()
                
                if choice == '1':
                    self.start_app_monitoring(180)
                elif choice == '2':
                    self.start_keylogger(180)
                elif choice == '3':
                    self.full_monitoring(180)
                elif choice == '4':
                    self.config.print_settings()
                elif choice == '5':
                    self.show_installed_apps()
                elif choice == '6':
                    self.show_running_apps()
                elif choice == '7':
                    print("\nExiting Spyglass test...\n")
                    break
                else:
                    print("\nInvalid choice. Please select between 1-7.\n")
            else:
                print(f"Security Mode: LOW (App Monitoring Only)\n")
                print("1. Start App Monitoring Test (180 seconds)")
                print("2. Show Current Settings")
                print("3. View Installed Apps")
                print("4. View Running Apps")
                print("5. Exit Test\n")
                
                choice = input("Select option (1-5): ").strip()
                
                if choice == '1':
                    self.start_app_monitoring(180)
                elif choice == '2':
                    self.config.print_settings()
                elif choice == '3':
                    self.show_installed_apps()
                elif choice == '4':
                    self.show_running_apps()
                elif choice == '5':
                    print("\nExiting Spyglass test...\n")
                    break
                else:
                    print("\nInvalid choice. Please select between 1-5.\n")
    
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
        if self.database:
            self.database.closeDB()
        if self.app_monitor:
            self.app_monitor.cleanup()
        if self.keystroke_monitor and self.keystroke_monitor.listener:
            self.keystroke_monitor.stopLog()


def main():
    # App Entry Point
    """Main entry point for the Spyglass test """
    # Setup file logging with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    reports_dir = os.path.join(os.path.dirname(__file__), 'Reports')
   
    # make the folder if it doesn't exist
    os.makedirs(reports_dir, exist_ok=True)
    log_file = os.path.join(reports_dir, f'spyglass_test_{timestamp}.log')
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
