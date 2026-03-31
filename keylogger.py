import logging
import datetime
import sys
import time
import os

from keystroke_monitor import KeystrokeMonitor
from database import DatabaseManager, insertIntoKeystrokeSummaryTable

class Keylogger:
    def __init__(self, app=None):
        self.adminHandler = getattr(app, 'adminHandler', None)
        self.consent = getattr(app, 'consent', None)
        self.config = getattr(app, 'config', None)
        self.database = getattr(app, 'database', None)
        self.keylogger = None
        self.last_session_keystrokes = {}
        self.monitoring_level = getattr(app, 'monitoring_level', None)
        self.is_running = False
        self.start_time = None
    
    def run(self) -> bool:
        #Run the complete keylogger flow

        # Step 5: Check if keylogging is enabled before running test
        logging.info("Starting keylogging status check...")
        if self.config.is_keylogger_enabled():
            print("\nKeystroke logging is ENABLED (HIGH monitoring level)")
            logging.info("Keystroke logging is ENABLED")
        else:
            print("\nKeystroke logging is DISABLED (LOW monitoring level)")
            logging.info("Keystroke logging is DISABLED")
        
        print("\n" + "="*70)
        print("INITIALIZATION COMPLETE".center(70))
        print("="*70 + "\n")
        
        logging.info("Setup Completed successfully")
        return True
    
    
    def start_keylogger(self) -> bool:
        # Start keystroke logging
        if not self.config.is_keylogger_enabled():
            print("\nKeystroke logging is not enabled.\n Monitoring Level: LOW")
            print("To enable keystroke logging, restart the app and select HIGH monitoring level.\n")
            logging.warning("Keystroke logging is disabled. Monitoring level: LOW")
            return False

        print("\n" + "="*70)
        print("KEYSTROKE LOGGER".center(70))
        print("="*70 + "\n")

        print("Starting keystroke monitoring...")
        logging.info("Starting keystroke monitoring")

        try:
            reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Reports')
            log_path = os.path.join(reports_dir, 'keystrokes.log')
            self.keylogger = KeystrokeMonitor(log_file=log_path)

            if not self.keylogger.startLog():
                print("Failed to start keystroke monitoring.\n")
                logging.error("Failed to start keystroke monitoring")
                return False

            self.is_running = True
            self.start_time = datetime.datetime.now()
            print("Keystroke monitoring started. Use 'Stop Monitoring' to end.\n")
            logging.info("Keystroke monitoring successfully started")
            return True
        except Exception as e:
            print(f"\nError starting keystroke monitoring: {e}\n")
            logging.error(f"Error starting keystroke monitoring: {e}", exc_info=True)
            return False

    def stop_keylogger(self) -> bool:
        # Stop keystroke logging on demand
        if not self.is_running or not self.keylogger:
            logging.warning("Keystroke monitoring is not running.")
            return False

        with self.keylogger.lock:
            self.last_session_keystrokes = self.keylogger.keystrokes.copy()

        self.keylogger.stopLog()
        self.is_running = False
        elapsed = int((datetime.datetime.now() - self.start_time).total_seconds()) if self.start_time else 0
        logging.info("Keystroke monitoring stopped")
        print("\nKeystroke monitoring stopped.\n")

        self.update_keystroke_summaryDB(duration=elapsed)
        self.display_keylogger_results()

        # Flush logging
        for handler in logging.root.handlers:
            handler.flush()
        keystroke_logger = logging.getLogger('keystrokes')
        for handler in keystroke_logger.handlers:
            handler.flush()

        return True
    
    def display_keylogger_results(self) -> None:
        # Display keystroke logging results# 
        keystroke_logger = logging.getLogger('keystrokes')
        
        if not self.keylogger:
            logging.warning("No keylogger instance available for results")
            return
        
        print("="*70)
        print("KEYLOGGER RESULTS".center(70))
        print("="*70 + "\n")
        
        keylogger_data = self.keylogger.keystrokes
        if not keylogger_data and self.last_session_keystrokes:
            keylogger_data = self.last_session_keystrokes
        logging.info(f"DEBUG: keylogger_data = {keylogger_data}")
        logging.info(f"DEBUG: keylogger_data type = {type(keylogger_data)}")
        logging.info(f"DEBUG: keylogger_data length = {len(keylogger_data)}")
        
        if not keylogger_data:
            print("No keystrokes were recorded during the test period.\n")
            logging.warning("No keystrokes recorded during the test period")
            keystroke_logger.warning("No keystrokes recorded during the test period")
            return
        
        total_keys = sum(keylogger_data.values())
        print(f"Total keystrokes captured: {total_keys}\n")
        
        keystroke_logger.info("="*70)
        keystroke_logger.info(f"KEYSTROKE TEST RESULTS - Total keystrokes captured: {total_keys}")
        keystroke_logger.info("="*70)
        
        print("Keystroke Frequency")
        print("-" * 70)
        
        # Sort by frequency
        sorted_keys = sorted(keylogger_data.items(), key=lambda x: x[1], reverse=True)
        
        keystroke_logger.info("Top 20 Keystroke Frequencies:")
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
            bar = "=" * bar_length
            print(f"  {key_display:20s} {count:4d} {bar}")
            keystroke_logger.info(f"  {key_display:20s} {count:4d}")
        
        keystroke_logger.info("="*70)
        keystroke_logger.info(f"ALL CAPTURED KEYSTROKES ({len(keylogger_data)} unique keys):")
        keystroke_logger.info("="*70)
        for key, count in sorted(keylogger_data.items(), key=lambda x: x[1], reverse=True):
            keystroke_logger.info(f"  {key}: {count}")
        
        print("\n" + "="*70 + "\n")

    def resolve_user_id(self):
        if not self.database or not getattr(self.database, 'connection', None):
            return None

        try:
            cursor = self.database.connection.cursor()
            cursor.execute("SELECT userID FROM user ORDER BY createdAt DESC LIMIT 1")
            row = cursor.fetchone()
            cursor.close()
            if row and row[0]:
                return row[0]
        except Exception as e:
            logging.error(f"Failed to resolve user ID for keystroke summary: {e}")

        return None

    def create_keystroke_event(self, duration: int):
        if not self.database or not getattr(self.database, 'connection', None):
            return None

        user_id = self._resolve_user_id()
        if not user_id:
            return None

        try:
            cursor = self.database.connection.cursor()
            cursor.execute(
                """
                INSERT INTO application (appName, executablePath, vendor)
                VALUES (?, ?, ?)
                ON CONFLICT(executablePath) DO UPDATE SET
                    appName = excluded.appName,
                    vendor = excluded.vendor
                """,
                ("Keylogger Session", "INTERNAL::KEYLOGGER", "Spyglass")
            )
            self.database.connection.commit()

            cursor.execute(
                "SELECT appID FROM application WHERE executablePath = ? LIMIT 1",
                ("INTERNAL::KEYLOGGER",)
            )
            app_row = cursor.fetchone()
            if not app_row or app_row[0] is None:
                cursor.close()
                return None

            cursor.execute(
                """
                INSERT INTO activity_log (userID, appID, action, category, reason, duration)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, int(app_row[0]), "keystroke_test_completed", "monitoring", "Keylogger test ended", duration)
            )
            event_id = cursor.lastrowid
            self.database.connection.commit()
            cursor.close()
            return int(event_id) if event_id is not None else None
        except Exception as e:
            logging.error(f"Failed to create keystroke activity event: {e}", exc_info=True)
            return None

    def update_keystroke_summaryDB(self, duration: int) -> None:
        if not self.last_session_keystrokes:
            logging.info("No keystrokes captured; skipping keystroke summary DB append")
            return

        event_id = self.create_keystroke_event(duration)
        if event_id is None:
            logging.warning("Unable to create activity event; skipping keystroke summary DB append")
            return

        key_count = sum(self.last_session_keystrokes.values())
        keys_per_minute = int((key_count / max(duration, 1)) * 60)

        categories = set()
        for key in self.last_session_keystrokes.keys():
            if isinstance(key, str) and key.startswith('Key.'):
                categories.add('special')
            elif isinstance(key, str) and len(key) == 1 and key.isalpha():
                categories.add('letters')
            elif isinstance(key, str) and len(key) == 1 and key.isdigit():
                categories.add('numbers')
            else:
                categories.add('other')

        interval_end = datetime.datetime.now()
        interval_start = interval_end - datetime.timedelta(seconds=duration)

        success = insertIntoKeystrokeSummaryTable(
            eventID=event_id,
            intervalStart=interval_start.isoformat(timespec='seconds'),
            intervalEnd=interval_end.isoformat(timespec='seconds'),
            keyCount=key_count,
            keysPerMinute=keys_per_minute,
            keyCategories=", ".join(sorted(categories)) if categories else None,
            idleSeconds=0,
        )

        if success:
            logging.info(f"Keystroke summary appended to database (eventID={event_id})")
        else:
            logging.warning("Keystroke summary append failed")


