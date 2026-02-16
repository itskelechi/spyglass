import sys
import pathlib

import KeystrokeMonitor 

class SpyglassApp:
    print("Initializing SpyglassApp...")
    
    def __init__(self):
        #Main application class
        self.keystroke_monitor = KeystrokeMonitor()
        
    def startMonitoring(self):
        #Start monitoring keystrokes
        print("Starting SpyglassApp monitoring...")
        
        if self.keystroke_monitor.startLog():
            print("Keystroke monitoring started successfully.")
        else:
            print("Failed to start keystroke monitoring.")
            sys.exit(1)
        print("SpyglassApp is now monitoring keystrokes.")
        print("Privacy Warning: This application collects keystroke data. Ensure you have the necessary permissions to run this software.")
        
    def stopMonitoring(self):
        #Stop monitoring keystrokes
        print("Stopping SpyglassApp monitoring...")
        
        if self.keystroke_monitor.listener:
            self.keystroke_monitor.stopLog()
            print("Keystroke monitoring stopped successfully.")
        else:
            print("Keystroke monitoring was not running.")
        
    def generateReports(self):
        #Show reports of monitored data
        print("Generating SpyglassApp report...")
        
        with self.keystroke_monitor.lock:
            if not self.keystroke_monitor.keystrokes:
                print("No keystrokes recorded.")
                return
            
            print("Keystroke Report:")
            for key, count in self.keystroke_monitor.keystrokes.items():
                print(f"{key}: {count} times")
    
    def systemInfo(self):
        #Show system information
        print("Gathering system information...")
        
        import platform
        import psutil
        
        print(f"System: {platform.system()} {platform.release()}")
        print(f"Processor: {platform.processor()}")
        print(f"CPU Usage: {psutil.cpu_percent()}%")
        print(f"Memory Usage: {psutil.virtual_memory().percent}%")
        
    def run(self) -> None:
        #App start
        while True:
            print("\nSpyglassApp Menu:")
            print("1. Start Monitoring")
            print("2. Stop Monitoring")
            print("3. Show Analytics")
            print("4. Show Reports")
            
            choice = input("Select an option (1-4): ")
            
            if choice == '1':
                self.startMonitoring()
            elif choice == '2':
                self.stopMonitoring()
            elif choice == '3':
                #Analytics placeholder
                print("Analytics feature is under development.")
            elif choice == '4':
                self.generateReports()
            else:
                print("Invalid choice. Please select a valid option.")
                
                
    

SpyglassApp = SpyglassApp()
SpyglassApp.run()
