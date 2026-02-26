# 
# Spyglass Main Application Entry Point
# For keylogger testing, run: python keylogger.py
# 

import sys


def main():
    # Main entry point# 
    print(""" 
╔════════════════════════════════════════════════════════════════╗
║                      SPYGLASS APPLICATION                      ║
╚════════════════════════════════════════════════════════════════╝

For keystroke logging testing and setup, please run:

    python keylogger.py

This will guide you through:
  1. User Consent Screen
  2. Monitoring Level Selection (LOW/HIGH)
  3. Configuration Setup
  4. Database Initialization
  5. Keystroke Logging Tests

═══════════════════════════════════════════════════════════════════
    """)
    
    # Optional: Ask if user wants to run test
    choice = input("Would you like to start the keystroke logging test? (y/n): ").strip().lower()
    
    if choice == 'y':
        try:
            from keylogger import main as run_test
            run_test()
        except Exception as e:
            print(f"Error running test: {e}")
            sys.exit(1)
    else:
        print("\nExiting Spyglass.")
        sys.exit(0)


if __name__ == "__main__":
    main()
