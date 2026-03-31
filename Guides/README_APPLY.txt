SpyGlass threshold monitoring fix package

Included files:
- spyglass.py
- alert_manager.py
- threshold_engine.py
- appMonitor.py
- keystroke_monitor.py
- configSettings.py

What changed:
- Added threshold-based monitoring for application/process and keystroke activity
- Added alert cooldowns and a startup grace period so alerts are not too easy to trigger
- Raised SpyGlass self-CPU threshold to 50%
- Reduced noisy unknown-application alerts by ignoring common Windows/system processes
- Fixed the missing start_integrated_test path in spyglass.py
- Added MEDIUM support in config settings

How to apply:
1. Back up your current project folder.
2. Copy these files into your SpyGlass folder.
3. Replace the existing files when prompted.
4. Run:
   python spyglass.py

Notes:
- Alerts are shown through the existing console/logging flow plus a Windows popup.
- Database encryption still depends on sqlcipher3 being available. If it is not installed, the app will fall back to standard sqlite3.
