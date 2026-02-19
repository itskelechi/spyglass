# Spyglass Keystroke Logging

Focused script for keystroke logging functionality with consent screen, monitoring level selection, and encrypted database.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the test
python keylogger.py
```

### 1. Admin Privilege Check
- Detects if running as Administrator
- Requests UAC elevation if needed
- Continues with elevated privileges

### 2. Consent Screen
Displays detailed consent information including:
- Monitoring disclosure
- Privacy & data usage terms
- Admin privilege requirements

You must select a monitoring level:
- **[1] LOW**: Basic monitoring only (processes, system info)
- **[2] HIGH**: Full monitoring including keystroke logging  

### 3. Configuration Setup
- Settings saved to `spyglass_settings.json`
- Monitoring level determines features:
  - LOW: No keystroke logging
  - HIGH: Keystroke logging enabled

### 4. Database Initialization
- Creates encrypted SQLCipher database
- Initializes user table
- Ready for data storage

## Keystroke Test Menu

After initialization (if HIGH level selected):

```
1. Start Keystroke Test (30 seconds)
2. Start Keystroke Test (60 seconds)
3. Show Current Settings
4. Exit Test
```

### Testing Keystroke Logging

When you run a keystroke test:
1. Monitoring starts and counts down
2. Type freely on your keyboard
3. All keystrokes are captured and analyzed
4. Results displayed showing frequency of each key

Example output:
```
KEYSTROKE LOGGING RESULTS
═══════════════════════════════════════════════════════════════════

Total keystrokes captured: 243

Keystroke Frequency (Top 20):
─────────────────────────────────────────────────────────────────
  'e'                   42 ████████████████████████████████░░░░░░░
  't'                   38 ███████████████████████████░░░░░░░░░░░░░
  'a'                   35 ████████████████████████░░░░░░░░░░░░░░░
  ' ' (SPACE)           32 ████████████████████░░░░░░░░░░░░░░░░░░░
  ...
```

## Project Files

### Core Test Files
- **keylogger.py** - Main test script (START HERE)
- **consent.py** - User consent & monitoring level selection
- **configSettings.py** - Configuration management
- **keylogger.py** - Keystroke capture and analysis

### Infrastructure Files
- **database.py** - SQLCipher encrypted database with SQLAlchemy ORM
- **adminHandler.py** - Windows admin privilege handling
- **userInfo.py** - System information gathering
- **main.py** - Quick start entry point

### Configuration Files
- **requirements.txt** - Python dependencies
- **config.ini** - Configuration template
- **spyglass_settings.json** - Auto-generated settings file

## Database Setup

The encrypted database stores configuration in the user table:

```sql
CREATE TABLE user (
  userID INTEGER PRIMARY KEY, -- machineId
  userSystem TEXT,           -- OS info
  username TEXT,             -- hostname
  systemInfo TEXT,           -- device info as JSON
  email TEXT,
  processor TEXT,
  passwordHash TEXT,
  createdAt TEXT
);
```

## Configuration File

`spyglass_settings.json` contains:

```json
{
  "monitoring_level": "HIGH",
  "keystroke_logging_enabled": true,
  "app_monitoring_enabled": true,
  "screenshot_interval": 0,
  "max_storage_mb": 1000,
  "debug_logging": false,
  "auto_backup_enabled": false,
  "database_encryption": true
}
```

## Requirements

```
sqlalchemy==2.0.23
psutil==5.9.6
pynput==1.7.6
cryptography==41.0.7
sqlcipher3-binary==3.46.1
```

## Important Notes

1. **Admin Privileges Required**: Application needs Windows Administrator to monitor keystrokes
2. **Encrypted Storage**: All data stored in SQLCipher-encrypted `spyglass.db`
3. **Consent-Driven**: Users must explicitly choose monitoring level
4. **Local Storage**: Data remains on device by default
5. **Privacy**: Review consent screen carefully before selecting HIGH monitoring

## Troubleshooting

### "Database is locked" error
- Close all instances of the application
- Delete or backup `spyglass.db`
- Run test again

### Keystroke logging not capturing
- Ensure you selected HIGH monitoring level
- Rerun test and select HIGH monitoring
- Make sure application has admin privileges

### Admin privileges not escalating
- Run Command Prompt as Administrator first
- Then run `python keylogger.py`

### Import errors
- Run: `pip install -r requirements.txt`
- Verify Python 3.8+

## Testing Tips

1. **First Run**: Select LOW monitoring to verify basic setup works
2. **Full Test**: Restart and select HIGH monitoring for keystroke test
3. **Monitor Resources**: Watch task manager during keystroke test
4. **Settings**: Check `spyglass_settings.json` to verify configuration
5. **Database**: Encrypted database `spyglass.db` stores persistent data

## Example Test Session

```bash
$ python keylogger.py

[Step 1/4] Checking Administrator Privileges...
Current privilege level: Admin
Administrator privileges confirmed.

[Step 2/4] User Consent & Monitoring Level Selection...
# ... consent screen displays ...
Enter your choice (1-3): 2

# ... configuration setup ...

[Step 4/4] Initializing Encrypted Database...
Database initialized with SQLCipher encryption and verified.

INITIALIZATION SUCCESSFUL

KEYSTROKE LOGGING TEST MENU
═══════════════════════════════════════════════════════════════════

Monitoring Level: HIGH
Keystroke Logging: ENABLED

1. Start Keystroke Test (30 minutes)
2. Start Keystroke Test (60 minutes)
3. Show Current Settings
4. Exit Test

Select option (1-4): 1

# ... keylogger runs ...
# ... results displayed ...
```

