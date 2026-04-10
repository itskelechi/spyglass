import os
import datetime
import logging
from pynput import keyboard
from typing import Dict, Optional
import threading

### Keystroke Monitor Class - for App

class KeystrokeMonitor:
    #Monitor keystrokes
    
    def __init__(self, time_interval: int = 60, log_file: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Reports', 'keystrokes.log')):
        print("Initializing KeystrokeMonitor...")
        
        self.running = False
        self.time_interval = time_interval
        self.log_file = log_file
        self.keystrokes: Dict[str, int] = {}
        self.lock = threading.Lock()
        self.interval_start = datetime.datetime.now()
        self.listener: Optional[keyboard.Listener] = None
        self.last_key: Optional[str] = None
        
    def on_press(self, key):
        try:
            keyStr = key.char
        except AttributeError:
            keyStr = str(key)
        with self.lock:
            self.keystrokes[keyStr] = self.keystrokes.get(keyStr, 0) + 1
            self.last_key = keyStr
        logging.getLogger('keystrokes').info(f"Key: {keyStr}")
        
    def on_click(self, x,y):
        with self.lock:
            self.keystrokes['Mouse Click'] = self.keystrokes.get('Mouse Click', 0) + 1
    
    def updateLog(self, string: str):
        self.interval_start = datetime.datetime.now()
        with open(self.log_file, 'a') as l:
            l.write(f"{self.interval_start} - {string}\n")
    
    def updateDatabase(self, key):
        #update database with summary keystroke log
        with self.lock:
            self.keystrokes.clear()
            
    #requires admin privileges to run
    def startLog(self) -> bool:
        if self.running:
            print("Keystroke Monitor is already running.")
            #throw user alert
            return False

        print("Starting Keystroke Monitor...")
        
        self.running = True
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        return True
    
    def stopLog(self):
        if not self.running:
            print("Keystroke Monitor is not running.")
            return
        
        print("Stopping Keystroke Monitor...")
        
        self.running = False
        if self.listener:
            self.listener.stop()
        self.updateLog(f"Keystrokes: {self.keystrokes}")
        self.updateDatabase(self.keystrokes)
        print("Keystroke Monitor stopped and data logged.")
    