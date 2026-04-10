# 
# Consent Screen Module
# Displays user consent for monitoring and collects permission acknowledgment
# 

import os

class ConsentScreen:
    # Handle user consent for monitoring activities
    def __init__(self):
        self.user_consented = False
        self.monitoring_level = None
        self.thresholds = {}
    
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
                self.show_threshold_settings()
                
                self.show_confirmation('LOW')
                return True
            elif choice == '2':
                self.monitoring_level = 'HIGH'
                self.user_consented = True
                self.show_threshold_settings()
                
                self.show_confirmation('HIGH')
                return True
            elif choice == '3':
                self.show_denial()
                return False
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    
    def show_confirmation(self, level: str) -> None:
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
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_monitoring_level(self) -> str:
        return self.monitoring_level if self.user_consented else None
    
    def is_keylogging_enabled(self) -> bool:
        return self.monitoring_level == 'HIGH'
    
    def was_consent_given(self) -> bool:
        return self.user_consented

    def show_threshold_settings(self) -> None:
        # Display threshold settings for monitoring/alerts then collect input
        self.clear_screen()
        print("=" * 70)
        print("MONITORING THRESHOLD SETTINGS".center(70))
        print("=" * 70)
        print("""
╔════════════════════════════════════════════════════════════════════╗
║                        SET YOUR THRESHOLDS                         ║
╚════════════════════════════════════════════════════════════════════╝

Set thresholds for monitoring activities to receive alerts when certain
conditions are met. Each threshold has 4 severity levels:

    LOW      → Informational alert
    MEDIUM   → Warning alert
    HIGH     → Elevated alert
    CRITICAL → Urgent alert

Press ENTER at any prompt to accept the Spyglass system default.

BASIC:
    • CPU Usage Threshold: 
        Alert when CPU usage exceeds a specified percentage
    • Memory Usage Threshold: 
        Alert when memory usage exceeds a specified percentage
    • Process Activity Threshold: 
        Alert when non-device processes are executed more than a certain number of times
    • Same-App Script Limit:
        Alert when one app spawns too many scripts
ADVANCED:
    • BASIC THRESHOLDS +
    • Keystroke Frequency Threshold: 
        Alert when a specific key is pressed more than a certain number of times 
    • Modifier Key Combination Threshold: 
        Alert when specific key combinations are used more than a certain number of times

EXPERT (FUTURE FEATURE):
    • BASIC + ADVANCED THRESHOLDS +
    • Custom Signature Matching: 
        Alert when specific patterns or signatures are detected in monitored data
    • Anomaly Detection Threshold: 
        Alert when unusual activity patterns are detected based on machine learning models
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
        input("Press ENTER to configure thresholds...")
        self.set_thresholds()

    def set_thresholds(self) -> None:
        self.clear_screen()
        print("=" * 70)
        print("CONFIGURE THRESHOLDS".center(70))
        print("=" * 70 + "\n")

        # BASIC — both LOW and HIGH
        print("  ── CPU Usage Threshold (%) ──")
        self.thresholds['cpu_limit'] = self.get_severity_inputs(
            "CPU %", defaults={'low': 60, 'medium': 75, 'high': 90, 'critical': 95},
            min_val=1, max_val=100)

        print("\n  ── Memory Usage Threshold (%) ──")
        self.thresholds['memory_limit'] = self.get_severity_inputs(
            "Memory %", defaults={'low': 60, 'medium': 75, 'high': 85, 'critical': 95},
            min_val=1, max_val=100)

        print("\n  ── Process Activity Threshold (simultaneous scripts) ──")
        self.thresholds['process_activity'] = self.get_severity_inputs(
            "Script count", defaults={'low': 20, 'medium': 50, 'high': 100, 'critical': 200},
            min_val=1, max_val=500)

        print("\n  ── Same-App Script Limit ──")
        self.thresholds['same_script_limit'] = self.get_severity_inputs(
            "Same-app scripts", defaults={'low': 5, 'medium': 10, 'high': 20, 'critical': 50},
            min_val=1, max_val=200)

        # ADVANCED — HIGH only
        if self.monitoring_level == 'HIGH':
            print("\n  ── Keystroke Frequency (keys/min) ──")
            self.thresholds['keystroke_frequency'] = self.get_severity_inputs(
                "Keys/min", defaults={'low': 200, 'medium': 360, 'high': 500, 'critical': 700},
                min_val=1, max_val=2000)

            print("\n  ── Modifier Key Combination Threshold (per interval) ──")
            self.thresholds['modifier_key_threshold'] = self.get_severity_inputs(
                "Modifier combos", defaults={'low': 10, 'medium': 25, 'high': 50, 'critical': 100},
                min_val=1, max_val=500)

        print("\n  Thresholds configured successfully!\n")
        input("Press ENTER to continue...")

    def get_severity_inputs(self, label: str, defaults: dict, min_val: int, max_val: int) -> dict:
        """Prompt for low/medium/high/critical values for a single threshold."""
        result = {}
        for severity in ('low', 'medium', 'high', 'critical'):
            result[severity] = self._get_numeric_input(
                f"    {label} [{severity.upper()}]",
                default=defaults[severity],
                min_val=min_val, max_val=max_val)
        return result

    def _get_numeric_input(self, prompt: str, default: int, min_val: int, max_val: int) -> int:
        while True:
            raw = input(f"  {prompt} [default: {default}]: ").strip()
            if raw == '':
                print(f"      → Using default: {default}")
                return default
            try:
                val = int(raw.replace('%', ''))
                if min_val <= val <= max_val:
                    return val
                print(f"      Must be between {min_val} and {max_val}.")
            except ValueError:
                print("      Please enter a valid number.")

    def get_thresholds(self) -> dict:
        return self.thresholds
        