import os
import datetime
from pynput import keyboard
from typing import Dict, Optional
import threading

class KeystrokeMonitor:
    #Monitor keystrokes
    
    def __init__(self, time_interval: int = 60, log_file: str = "keystrokes.log"):
       print("Initializing KeystrokeMonitor...")
        
        self.running = False
        self.time_interval = time_interval
        self.log_file = log_file
        self.keystrokes: Dict[str, int] = {}
        self.lock = threading.Lock()
        self.interval_start = datetime.datetime.now()
        self.listener: Optional[keyboard.Listener] = None
        self.last_key: Optional[str] = None
        
     
    
    #requires admin privileges to run
    def startLog(self) -> bool:
        if self.running:
            print("Keystroke Monitor is already running.")
            #throw user alert
            return False

        print("Starting Keystroke Monitor...")
        
    
    
    