import threading
from datetime import datetime
from typing import Dict, Any, Optional
import logging

import userInfo
from consent import ConsentScreen
from database import updateActivityLogTable, updateMonitoringSettingsTable, updateReportTable, updateAppTable, updateAlertTable, updatePrivacyThresholdTable
from adminHandler import AdminHandler

class AppMonitor:
    def __init__(self):
        self.adminHandler = None 
        self.consent = None
        self.config = None
        self.processMonitor = None
        self.monitoring_level = None
        self.is_running = False
    
        self.thread: Optional[threading.Thread] = None 
        self.current_process: Optional[Dict[str, Any]] = None
        self.last_update: Optional[datetime] = None
        self.poll_interval = 15.0  # seconds
    
    def run(self) -> bool:
        # Start the process monitoring in a separate thread#
        print("\n" + "="*70)
        print("SPYGLASS APP MONITOR - SETUP".center(70))
        print("="*70 + "\n")
        
        logging.info("Starting App Monitor setup - Checking admin privileges...")
        if not self.verify_admin():
            logging.error("Step 1 Failed: Admin verification failed")
            return False
        logging.info("Admin privileges verified successfully")
        
        logging.info("Starting App Monitor setup - Checking user consent...")
        if not self.check_consent():
            logging.error("Step 2 Failed: User consent not obtained")
            return False
        logging.info("User consent obtained successfully")
        
        if not self.get_config():
            logging.info("Starting App Monitor setup - Setting up configuration...")
            if not self.setup_config():
                logging.error("Step 3 Failed: Configuration setup failed")
                return False    
            logging.info("Configuration setup completed successfully")
        
        if self.thread and self.thread.is_alive():
            print("Process monitoring is already running.")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._monitor_processes, daemon=True)
        self.thread.start()
    