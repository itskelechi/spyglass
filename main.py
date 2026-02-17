import sys
import pathlib
from keystroke_monitor import KeystrokeMonitor
from initialization import run_initialization


class SpyglassApp:
    """Main application class"""
    
    def __init__(self, initializer):
        """Initialize SpyglassApp"""
        print("Initializing SpyglassApp...")
        self.keystroke_monitor = KeystrokeMonitor()
        self.initializer = initializer
        self.is_running = False
        
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
        """Run the main application menu"""
        self.is_running = True
        while self.is_running:
            print("\n" + "="*50)
            print("SPYGLASS MONITORING APPLICATION".center(50))
            print("="*50)
            print("1. Start Monitoring")
            print("2. Stop Monitoring")
            print("3. Show Analytics")
            print("4. Show Reports")
            print("5. Show Device Info")
            print("6. Exit")
            print("="*50)
            
            choice = input("Select an option (1-6): ").strip()
            
            if choice == '1':
                self.startMonitoring()
            elif choice == '2':
                self.stopMonitoring()
            elif choice == '3':
                print("Analytics feature is under development.")
            elif choice == '4':
                self.generateReports()
            elif choice == '5':
                device_info = self.initializer.get_device_info()
                if device_info:
                    import json
                    print("\nStored Device Information:")
                    print(json.dumps(device_info, indent=2))
            elif choice == '6':
                print("Exiting Spyglass...")
                self.is_running = False
            else:
                print("Invalid choice. Please select a valid option.")
    
    def close(self) -> None:
        """Close the application and clean up resources"""
        if self.initializer:
            self.initializer.cleanup()


def main():
    """Main entry point for Spyglass application"""
    try:
        # Run initialization with admin privileges and device info retrieval
        initializer = run_initialization()
        
        # Start the main application
        app = SpyglassApp(initializer)
        app.run()
        app.close()
        
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
