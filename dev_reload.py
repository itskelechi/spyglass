"""Dev helper — auto-restarts spyglassGUI.py whenever a .py file changes."""
import subprocess, sys, os
from watchfiles import watch

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    proc = None
    try:
        proc = subprocess.Popen([sys.executable, "spyglassGUI.py"])
        print("[dev_reload] Started spyglassGUI.py — save any .py file to restart")
        for changes in watch(".", watch_filter=lambda _, path: path.endswith(".py")):
            print(f"[dev_reload] Change detected, restarting...")
            proc.terminate()
            proc.wait()
            proc = subprocess.Popen([sys.executable, "spyglassGUI.py"])
    except KeyboardInterrupt:
        print("\n[dev_reload] Stopped.")
    finally:
        if proc:
            proc.terminate()

if __name__ == "__main__":
    main()
