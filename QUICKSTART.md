# Spyglass Quick Start Guide

## Installation (2 minutes)

### Step 1: Install Python Requirements
```bash
pip install -r requirements.txt
```

Expected output:
```
Successfully installed sqlalchemy psutil pynput cryptography
```

### Step 2: Run Application
```bash
python main.py
```

## First Run (Automatic)

The application will automatically:
1. ✓ Request Windows admin privileges (UAC prompt - click "Yes")
2. ✓ Create encrypted database (`spyglass.db`)
3. ✓ Gather device information from your system
4. ✓ Display a summary of information retrieved
5. ✓ Store all data securely

This all happens automatically on startup!

## Main Menu Options

```
1. Start Monitoring    → Begin capturing keystrokes
2. Stop Monitoring     → Stop keystroke capture
3. Show Analytics      → View statistics (TBD)
4. Show Reports        → Generate monitoring reports
5. Show Device Info    → View stored system information
6. Exit                → Close the application
```

## What Gets Stored

### Device Information (Captured Once at Startup)
- Operating System (Windows version, build number)
- Hostname and Username
- CPU/Processor information
- RAM capacity
- Storage drives (capacity and usage)
- Network IP address
- MAC addresses
- Machine unique identifier

### During Monitoring
- Keystroke counts and patterns
- Application usage
- User activity logs
- Security alerts

## Generated Files

After running, you'll have:

```
spyglass/
├── spyglass.db              ← Your encrypted database (data storage)
├── .spyglass_key            ← Encryption key (keep secure!)
└── backups/                 ← Automatic backups (with encryption)
    └── spyglass_backup_*.db.encrypted
```

## Database Access

The data is stored in SQLite. To view, you can use:

### Option 1: Visual Studio Code
1. Install "SQLite" extension by alexcvzz
2. Right-click `spyglass.db` → "Open Database"
3. View tables and data

### Option 2: SQLite Command Line
```bash
sqlite3 spyglass.db
sqlite> SELECT * FROM device_info;
```

### Option 3: Python Script
```python
from database import getDB

db = getDB()
device_info = db.getDeviceInfo(user_id=1)
import json
print(json.dumps(device_info, indent=2))
```

## Common Tasks

### View Stored Device Information
```
Menu → Option 5 → Show Device Info
```

### Create Backup with Encryption
```python
from db_encryption import DatabaseEncryption

enc = DatabaseEncryption()
enc.backup_database("spyglass.db", "backups")
```

### Generate Keystroke Report
```
Menu → Option 1 → Start Monitoring
[Use your keyboard normally]
Menu → Option 2 → Stop Monitoring
Menu → Option 4 → Show Reports
```

### Securely Delete Files
```python
from db_encryption import secure_delete_file

secure_delete_file("spyglass.db")  # Overwrite 3 times then delete
```

## Configuration

Edit `config.ini` to customize:
- Keystroke logging enabled/disabled
- Screenshot interval
- Max storage size
- Backup frequency
- And more...

## Troubleshooting

### "Access Denied" Error
→ Run as Administrator: Right-click Command Prompt → "Run as administrator"

### "No module named..." Error
→ Install requirements: `pip install -r requirements.txt`

### Menu won't appear
→ Make sure admin privileges were granted in UAC prompt

### Database locked
→ Exit application, then: `del spyglass.db` to reset

## Features Overview

| Feature | Status | Details |
|---------|--------|---------|
| Admin Elevation | ✅ | Automatic UAC prompt |
| Device Info | ✅ | Full system snapshot |
| Encrypted DB | ✅ | SQLite with Fernet |
| Keylogging | ✅ | Real-time capture |
| Reporting | ✅ | Activity summaries |
| Backups | ✅ | Auto encrypted backups |
| Multi-threaded | ✅ | Concurrent operations |

## Files Breakdown

| File | Purpose |
|------|---------|
| `main.py` | Application entry point & menu |
| `initialization.py` | First-run setup wizard |
| `admin_handler.py` | Windows privilege management |
| `device_info.py` | System information gathering |
| `database.py` | Data storage & retrieval |
| `db_encryption.py` | Encryption utilities |
| `keystroke_monitor.py` | Keyboard event capture |

## Next Steps

1. ✅ Install requirements: `pip install -r requirements.txt`
2. ✅ Run app: `python main.py`
3. ✅ Click "Yes" on UAC prompt
4. ✅ Review device info displayed
5. ✅ Use menu to start/stop monitoring

## Need Help?

- **Installation issues**: See README.md → Troubleshooting
- **Feature questions**: Check IMPLEMENTATION_SUMMARY.md
- **Usage examples**: Look at code comments in each module
- **Configuration**: Edit config.ini

---

**Ready to go!** Just run `python main.py` and follow the prompts.
