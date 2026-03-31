Retuned SpyGlass alert files

This update reduces the false positives you reported:
- Discord should no longer trigger "Suspicious Application" just for opening.
- Safe/system processes no longer raise Performance Risk / Hidden Activity.
- Process count threshold is much higher.
- Startup grace and cooldown are longer.
- Unknown apps only alert when they show notable CPU usage.

Replace:
- threshold_engine.py
- alert_manager.py
- appMonitor.py

Then run:
python spyglass.py
