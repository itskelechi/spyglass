import sys
import time
import datetime
from typing import Dict, Any, Optional
import os
import logging
from pynput import keyboard

from consent import ConsentScreen
from configSettings import create_config, ConfigSettings
from database import DatabaseManager
from keystroke_monitor import KeystrokeMonitor
from adminHandler import AdminHandler


class Keylogger:
    
    def __init__(self):
        self.adminHandler = None
        self.consent = None
        self.config = None
        self.database = None
        self.keylogger = None
        self.monitoring_level = None
        self.is_running = False
    
    def run(self) -> bool:
        #Run the complete keylogger flow
        
        print("\n" + "*"*70)
        print("SPYGLASS KEYLOGGER - SETUP".center(70))
        print("*"*70 + "\n")
        
        # Step 1: Check admin privileges
        if not self.verify_admin():
            return False
        
        # Step 2: Display consent screen
        if not self.get_consent():
            return False
        
        # Step 3: Create config from consent
        if not self.setup_config():
            return False
        
        # Step 4: Initialize database
        if not self.setup_db():
            return False
        
        # Step 5: Check if keylogging is enabled before running test
        if self.config.is_keylogger_enabled():
            print("\nKeystroke logging is ENABLED (HIGH monitoring level)")
        else:
            print("\nKeystroke logging is DISABLED (LOW monitoring level)")
        
        print("\n" + "*"*70)
        print("INITIALIZATION COMPLETE".center(70))
        print("*"*70 + "\n")
        
        return True
    
    def verify_admin(self) -> bool:
        # Check and request admin privileges
        try:
            logging.info("Checking administrator privileges...")
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
            self.consent = ConsentScreen()
            if not self.consent.display_consent():
                print("\nConsent was not given. Test cannot continue.\n")
                return False
            
            self.monitoring_level = self.consent.get_monitoring_level()
            print(f"\nConsent received. Monitoring level: {self.monitoring_level}\n")
            return True
        except Exception as e:
            print(f"\nError during consent: {e}\n")
            return False
    
    def setup_config(self) -> bool:
        # Create and setup configuration from consent# 
        try:
            print("Configuring Monitoring Settings...\n")
            self.config = create_config(self.monitoring_level)
            self.config.print_settings()
            return True
        except Exception as e:
            print(f"\nError setting up config: {e}\n")
            return False
    
    def setup_db(self) -> bool:
        # Initialize the database# 
        try:
            print("Initializing Encrypted Database...\n")
            import hashlib
            encryption_key = hashlib.sha256(b"spyglass_secure_key_v1").hexdigest()
            
            self.database = DatabaseManager()
            self.database.initializeDB(create_tables=True, encryption_key=encryption_key)
            
            if not self.database.verifyConnection():
                return False
            
            print("Database initialized with SQLCipher encryption and verified.\n")
            return True
        except Exception as e:
            print(f"\nError setting up database: {e}\n")
            return False
    
    def start_keylogger(self, duration: int = 1800) -> bool:
        # Start keystroke logging# 
        if not self.config.is_keylogger_enabled():
            print("\nKeystroke logging is not enabled.\n Monitoring Level: LOW")
            print("To enable keystroke logging, restart the app and select HIGH monitoring level.\n") # change with config setting
            logging.warning("Keystroke logging is disabled. Monitoring level: LOW")
            return False
        
        print("\n" + "*"*70)
        print("KEYSTROKE LOGGER".center(70))
        print("*"*70 + "\n")
        
        print(f"Starting keystroke monitoring for {duration} seconds...")
        print("Type freely on your keyboard. All keystrokes will be captured and logged.\n")
        logging.info(f"Starting keystroke monitoring for {duration} seconds")
        
        try:
            self.keylogger = KeystrokeMonitor()
            
            if not self.keylogger.startLog():
                print("Failed to start keystroke monitoring.\n")
                logging.error("Failed to start keystroke monitoring")
                return False
            
            print("Keystroke monitoring started.")
            print(f"Monitoring will continue for {duration} seconds...\n")
            logging.info("Keystroke monitoring successfully started")
            
            # Monitor for specified duration
            for remaining in range(duration, 0, -1):
                sys.stdout.write(f"\r⏱  Remaining time: {remaining:2d} seconds")
                sys.stdout.flush()
                time.sleep(1)
            
            sys.stdout.write("\r" + " " * 40 + "\r")  # Clear the line
            
            self.keylogger.stopLog()
            logging.info("Keystroke monitoring stopped")
            
            print("\nKeystroke monitoring stopped.\n")
            
            # Display results
            self.display_keylogger_results()
            
            return True
        except Exception as e:
            print(f"\nError during keystroke test: {e}\n")
            logging.error(f"Error during keystroke test: {e}", exc_info=True)
            return False
    
    def display_keylogger_results(self) -> None:
        # Display keystroke logging results# 
        if not self.keylogger:
            return
        
        print("*"*70)
        print("KEYLOGGER RESULTS".center(70))
        print("*"*70 + "\n")
        
        keylogger_data = self.keylogger.keystrokes
        
        if not keylogger_data:
            print("No keystrokes were recorded during the test period.\n")
            logging.warning("No keystrokes recorded during the test period")
            return
        
        total_keys = sum(keylogger_data.values())
        print(f"Total keystrokes captured: {total_keys}\n")
        logging.info(f"Total keystrokes captured: {total_keys}")
        
        print("Keystroke Frequency (Top 20):")
        print("-" * 70)
        
        # Sort by frequency
        sorted_keys = sorted(keylogger_data.items(), key=lambda x: x[1], reverse=True)[:20]
        
        logging.info("Top keystroke frequencies:")
        for key, count in sorted_keys:
            # Format key display
            if key in ['Key.shift', 'Key.ctrl_l', 'Key.ctrl_r', 'Key.alt_l', 'Key.alt_r']:
                key_display = key.replace('Key.', '').upper()
            elif key == 'Key.space':
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
            bar = "█" * bar_length
            print(f"  {key_display:20s} {count:4d} {bar}")
            logging.info(f"  {key_display:20s} {count:4d}")
        
        print("\n" + "*"*70 + "\n")
    
    def show_menu(self) -> None:
        # Show test menu# 
        while True:
            print("*"*70)
            print("KEYSTROKE LOGGING TEST MENU".center(70))
            print("*"*70)
            print(f"\nMonitoring Level: {self.monitoring_level}")
            print(f"Keystroke Logging: {'ENABLED' if self.config.is_keylogger_enabled() else 'DISABLED'}\n")
            
            print("1. Start Keystroke Test (30 seconds)")
            print("2. Start Keystroke Test (60 seconds)")
            print("3. Show Current Settings")
            print("4. Exit Test\n")
            
            choice = input("Select option (1-4): ").strip()
            
            if choice == '1':
                self.start_keylogger(1800) #30 minutes
            elif choice == '2':
                self.start_keylogger(3600) #60 minutes
            elif choice == '3':
                self.config.print_settings()
            elif choice == '4':
                print("\nExiting keystroke test...\n")
                break
            else:
                print("\nInvalid choice. Please select between 1-4.\n")
    
    def cleanup(self) -> None:
        # Clean up resources# 
        if self.database:
            self.database.closeDB()
        if self.keylogger and self.keylogger.listener:
            self.keylogger.stopLog()


def main():
    """Main entry point for the keylogger application."""
    # Setup file logging with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(os.path.dirname(__file__), f'keylogger_activity_{timestamp}.log')
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logging.info("═" * 70)
    logging.info("KEYLOGGER APPLICATION STARTED")
    logging.info("═" * 70)
    
    try:
        logging.info("Initializing keylogger...")
        keylogger = Keylogger()
        logging.info("Running keylogger setup...")
        if keylogger.run():
            logging.info("Setup completed successfully. Showing menu...")
            keylogger.show_menu()
        else:
            logging.warning("Setup did not complete successfully.")
        logging.info("Cleaning up resources...")
        keylogger.cleanup()
        logging.info("Keylogger shutdown completed.")
    except KeyboardInterrupt:
        logging.info("Keylogger interrupted by user.")
        print("\n\nKeylogger interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()





