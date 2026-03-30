import psutil
import ctypes
import threading
import logging
import tkinter as tk
from datetime import datetime
from typing import Optional
from database import updateActivityLogTable, updateAlertTable

SCRIPTS_EXT = {'.exe', '.bat', '.cmd', '.ps1', '.vbs', '.js', '.py', '.gs', '.wsf', '.vbs'}

BLOCKLISTED_APPS = {
    #spyglass
    'spyglass.exe','spyglass.py',
    
    # remote access tools     
    'teamviewer.exe','anydesk.exe','logmein.exe','ultraviewer.exe', 'ammyy.exe',
    
    #network sniffers
    'wireshark.exe','tcpdump.exe','nmap.exe','fiddler.exe','netsh.exe', 
    
    #Credential harvesting
    'mimikatz.exe','hashcat.exe','john.exe','hydra.exe','crunch.exe', 'lazagne.exe',
    
    #Reverseshells
    'nc.exe','netcat.exe','ncat.exe','socat.exe','plink.exe','msfvenom.exe',
}

PASSWORD_KEYS = {'password', 'pass', 'sign in', 'login', 'auth', 'credentials', 'authentication'}

LOW_SECURITY = 'low'
MED_SECURITY = 'medium'
HIGH_SECURITY = 'high'
CRITICAL_SECURITY = 'critical'

class AlertEngine:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.is_running = False
        self.baseline_pids = set()
        self.alert_history = {}
        self.scan_thread = None
        self.lock = threading.Lock()
        self.pending_alerts = []
        self.polling_interval = 15  # seconds
    
    def start(self):
        if self.is_running:
            logging.warning("Alert Engine is already running.")
            return
        
        logging.info("Setting up Alert Engine with baseline snapshot...")
        self.baseline_pids = {p.pid for p in psutil.process_iter()}
        self.is_running = True
        self.scan_thread = threading.Thread(target=self.scan_loop, daemon=True)
        self.scan_thread.start()
        
    def stop(self):
        if not self.is_running:
            logging.warning("Alert Engine has stopped running.")
            return
        
        logging.info("Stopping Alert Engine...")
        self.is_running = False
    
    def scan_loop(self):
        #runs checks each polling interval
        while self.is_running:
            self.check_thresholds()
            threading.Event().wait(self.polling_interval)
            
    def check_thresholds(self):
        scripts = self.get_running_scripts()
        new_scripts = [s for s in scripts if s['pid'] not in self.baseline_pids]
        
        #LOW - NON SYSTEM SCRIPTS
        for script in new_scripts:
            self.raise_alert(
                LOW_SECURITY, 
                alert_type="background script", 
                key=f"bg_{script['pid']}",
                message=f"Background script detected: {script['name']} (PID {script['pid']})",
                app_name=script['name'], exe_path=script.get('exe', ''))
            
        #MEDIUM - 10+ SCRIPTS SIMULTANEOUSLY
        if len(scripts) >= 10:
            self.raise_alert(
                MED_SECURITY, 
                alert_type="excessive scripts", 
                key="script_volume",
                message=f"High number of background scripts detected: {len(scripts)}",
                app_name=script['name'], exe_path=script.get('exe', ''))
            
        #HIGH - 3+ SCRIPTS FROM SAME APP
        appCounts = {}
        for script in scripts:
            appCounts.setdefault(script['name'], []).append(script)
        for app, instances in appCounts.items():
            if len(instances) >= 3:
                self.raise_alert(
                    HIGH_SECURITY, 
                    alert_type="Suspicious App Behavior", 
                    key=f"AppFlood_{app}",
                    message=f"{len(instances)} background scripts from {app} detected",
                    app_name=app, exe_path=instances[0].get('exe', ''))
                
        #CRITICAL - BLOCKLISTED APPS
        for script in scripts:
            if script['name'].lower() in BLOCKLISTED_APPS:
                msg = 'Spyglass active monitoring is initiated' if 'spyglass' in script['name'].lower() else f"Blocklisted app detected: {script['name']}"
                self.raise_alert(
                    CRITICAL_SECURITY, 
                    alert_type="Blocklisted App Detected", 
                    key=f"Blocklist_{script['name']}",
                    message=f"Blocklisted app detected: {script['name']} (PID {script['pid']})",
                    app_name=script['name'], exe_path=script.get('exe', ''))
                
        #CRITICAL - password fields detected
        for title in self.get_all_windowTitles():
            if any(key in title.lower() for key in PASSWORD_KEYS):
                self.raise_alert(
                    CRITICAL_SECURITY, 
                    alert_type="Password Field Detected", 
                    key=f"PasswordFieldDetected_{title}",
                    message=f'Potential password field detected in window: "{title}"',
                    app_name=script['name'], exe_path=script.get('exe', ''))
                break
    def raise_alert(self, severity: str, alert_type: str, key: str, message: str, app_name: Optional[str] = None, exe_path: Optional[str] = None):
        #Log alert, update DB, show popup
        alertKey = (severity)