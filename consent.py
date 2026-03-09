# 
# Consent Screen Module
# Displays user consent for monitoring and collects permission acknowledgment
# 

import os
# from typing import bool_


class ConsentScreen:
    # Handle user consent for monitoring activities
    def __init__(self):
        self.user_consented = False
        self.monitoring_level = None
    
    def display_consent(self) -> bool:
        # Display consent screen and get user acknowledgment# 
        self.clear_screen()
        
        print("=" * 70)
        print("SPYGLASS - USER CONSENT & MONITORING AGREEMENT".center(70))
        print("=" * 70)
        print()
        print("""
╔════════════════════════════════════════════════════════════════════╗
║                    MONITORING DISCLOSURE                           ║
╚════════════════════════════════════════════════════════════════════╝

This application will monitor and log the following activities on your device:

BASIC MONITORING (All Levels):
  • Process/Application execution and activity
  • System performance metrics
  • Device information (OS, hardware, network)
  • General activity timestamps

ADVANCED MONITORING (High Level Only):
  • Keystroke activity (keyboard input tracking)
  • Character frequency analysis
  • Modifier key combinations
  
⚠️  IMPORTANT: This application captures sensitive input data.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRIVACY & DATA USAGE:
  • All data is stored locally on your device
  • Data is encrypted using SQLCipher
  • No data is transmitted without explicit consent
  • You can disable monitoring at any time
  • Data retention can be configured

ADMIN PRIVILEGES:
  • This application requires Windows Administrator privileges
  • Admin access is needed to monitor system-level activities
  • You will be prompted to grant permissions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

By continuing, you acknowledge that you understand and consent to the
monitoring activities described above.

╔════════════════════════════════════════════════════════════════════╗
║              SELECT YOUR MONITORING PREFERENCE                    ║
╚════════════════════════════════════════════════════════════════════╝

  [1] LOW    - Basic monitoring only (processes, system info)
  [2] HIGH   - Full monitoring (includes keystroke logging)
  [3] ABORT  - Decline consent and exit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
        
        while True:
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == '1':
                self.monitoring_level = 'LOW'
                self.user_consented = True
                self.show_confirmation('LOW')
                return True
            elif choice == '2':
                self.monitoring_level = 'HIGH'
                self.user_consented = True
                self.show_confirmation('HIGH')
                return True
            elif choice == '3':
                self.show_denial()
                return False
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    
    def show_confirmation(self, level: str) -> None:
        # Show confirmation of consent choice# 
        self.clear_screen()
        print("=" * 70)
        print("CONSENT CONFIRMED".center(70))
        print("=" * 70)
        print(f"\nYou have selected {level} monitoring level.")
        print("\nThe following activities will be monitored:")
        
        if level == 'LOW':
            print(""" 
                • Application/Process Activity
                • System Performance Metrics
                • Device Information
                • Activity Logs
            """)
        elif level == 'HIGH':
            print(""" 
                • Application/Process Activity
                • System Performance Metrics
                • Device Information
                • Activity Logs
                • KEYSTROKE LOGGING (enabled)
                • Input Pattern Analysis
            """)
        
        print("\nAll data will be encrypted and stored locally on your device.")
        print("You can disable monitoring at any time through the application menu.\n")
        
        input("Press ENTER to continue...")
    
    def show_denial(self) -> None:
        # Show denial message# 
        self.clear_screen()
        print("=" * 70)
        print("CONSENT DECLINED".center(70))
        print("=" * 70)
        print(""" 
            You have declined the monitoring consent.

            The application cannot continue without your consent.
            The application will now exit.

            Thank you for reviewing our monitoring policy.
        """)
        input("Press ENTER to exit...")
    
    def clear_screen(self) -> None:
        # Clear console screen 
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_monitoring_level(self) -> str:
        # Get the selected monitoring level 
        return self.monitoring_level if self.user_consented else None
    
    def is_keylogging_enabled(self) -> bool:
        # Check if keystroke logging is enabled (HIGH level only) 
        return self.monitoring_level == 'HIGH'
    
    def was_consent_given(self) -> bool:
        # Check if user gave consent 
        return self.user_consented
