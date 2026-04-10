"""Dev helper — auto-restarts spyglassGUI.py whenever a .py file changes."""
import subprocess, sys, os
from watchfiles import run_process

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_process(
        ".",                              # watch the whole project
        target=sys.executable,
        args=("spyglassGUI.py",),
        watch_filter=lambda _, path: path.endswith(".py"),
    )

if __name__ == "__main__":
    main()
