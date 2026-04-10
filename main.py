# 
# Spyglass Main Application Entry Point
# Usage:
#   python main.py         → Interactive terminal mode
#   python main.py --gui   → PyQt6 graphical interface
#   python main.py --cli   → Direct terminal mode (no prompt)
# 

import sys


def main():
    # Check for --gui / --cli flags
    if "--gui" in sys.argv:
        try:
            from spyglassGUI import run_gui
            run_gui()
        except ImportError as e:
            print(f"GUI dependencies missing. Install with: pip install PyQt6\n{e}")
            sys.exit(1)
        return

    if "--cli" in sys.argv:
        from spyglass import main as run_test
        run_test()
        return

    # Interactive mode — let user choose
    print(""" 
╔════════════════════════════════════════════════════════════════╗
║                      SPYGLASS APPLICATION                      ║
╚════════════════════════════════════════════════════════════════╝

  [1] Launch with Graphic Interface        (PyQt6 graphical interface)
  [2] Launch Terminal    (command-line interface)
  [3] Exit

═══════════════════════════════════════════════════════════════════
    """)
    
    choice = input("Select option (1-3): ").strip()
    
    if choice == '1':
        try:
            from spyglassGUI import run_gui
            run_gui()
        except ImportError as e:
            print(f"GUI dependencies missing. Install with: pip install PyQt6\n{e}")
            sys.exit(1)
    elif choice == '2':
        try:
            from spyglass import main as run_test
            run_test()
        except Exception as e:
            print(f"Error running test: {e}")
            sys.exit(1)
    else:
        print("\nExiting Spyglass.")
        sys.exit(0)


if __name__ == "__main__":
    main()
