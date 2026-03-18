# Spyglass - Device Monitoring & Keystroke Logger

A Windows-based device monitoring application with consent-driven monitoring levels, keystroke logging, and encrypted local data storage.

## Quick Start - Keystroke Logging Test

```bash
# Install dependencies
pip install -r requirements.txt

# Run App test
python spyglass.py
```

## Features

- **User Consent Screen**: Explicit permission request with monitoring level selection
- **Configurable Monitoring Levels**:
  - **LOW**: Basic process monitoring only
  - **HIGH**: Full monitoring including keystroke logging
  
- **Keystroke Logging** (HIGH level only):
  - Real-time keyboard input capture
  - Keystroke frequency analysis
  - Modifier key tracking
  - Privacy-conscious implementation

- **Encrypted Database**: SQLCipher encrypted local storage for all collected data
- **Windows Admin Privileges**: Automatic escalation for system-level monitoring
- **Device Information**: System details captured on initialization
- **Thread-Safe Operations**: Concurrent monitoring without conflicts

## System Requirements

- **OS**: Windows 7 or later
- **Python**: 3.8 or higher
- **Privileges**: Administrator (requested on startup)

## Installation

### 1. Clone or Download Project

```bash
# Navigate to project directory
cd spyglass
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required Packages**:
- `sqlalchemy` - Database ORM
- `psutil` - System information
- `pynput` - Keyboard monitoring
- `cryptography` - Encryption support
- `sqlcipher3-binary` - SQLite encryption

## Usage

### Run Keystroke Test (Recommended for Testing)

```bash
python spyglass.py
```

**What happens:**
1. **Consent Screen**: Review monitoring terms and select monitoring level
   - Select `1` for LOW (basic monitoring)
   - Select `2` for HIGH (includes keystroke logging)
   
2. **Configuration**: Settings are saved based on your selection

3. **Database Setup**: SQLCipher-encrypted database is initialized

4. **Keystroke Test Menu** (if HIGH level selected):
   - 30-second keystroke test
   - 60-second keystroke test  
   - View current settings
   - Exit

## Test Flow

```
┌─────────────────────────────────────────┐
│  Admin Privileges Check                 │
│  (Requests UAC elevation if needed)     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Consent & Monitoring Level Screen      │
│  - LOW: Process monitoring only         │
│  - HIGH: + Keystroke logging            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Configuration Setup                    │
│  Settings saved to spyglass_settings.json│
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Database Initialization                │
│  SQLCipher encryption enabled           │
│  User table created                     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Keystroke Test (HIGH level only)       │
│  - Capture keystrokes                   │
│  - Display frequency analysis           │
│  - Store encrypted in database          │
└─────────────────────────────────────────┘
```

## Core Modules

### `keylogger.py`
Main testing script that orchestrates:
- Admin privilege escalation
- Consent screen display
- Configuration management
- Database setup
- Keystroke test execution

### `consent.py`
Displays comprehensive consent form:
- Monitoring disclosure
- Privacy & data usage information
- Monitoring level selection
- User acknowledgment

### `configSettings.py`
Manages application configuration:
- Monitoring level (LOW/HIGH)
- Feature toggles
- Storage settings
- Loads/saves to `spyglass_settings.json`

### Core Modules

#### `main.py`
- Main entry point for the application
- Runs initialization sequence
- Provides interactive menu for monitoring controls

#### `initialization.py`
- Handles the 4-step initialization process:
  1. Requests administrator privileges
  2. Initializes the database
  3. Retrieves device information
  4. Stores device information encrypted in the database

#### `adminHandler.py`
- Checks current administrator status
- Handles UAC elevation requests
- Verifies admin privileges before allowing sensitive operations

#### `userInfo.py`
- Comprehensive device information gathering
- Retrieves system, hardware, network, storage, and processor info
- Returns both raw data and formatted summaries
- Data structure:
  ```json
  {
    "timestamp": "ISO 8601 timestamp",
    "system": { "os", "os_version", "os_build", "hostname", "username", ... },
    "hardware": { "machine_id", "processor_count", "total_ram_gb", ... },
    "network": { "hostname", "fqdn", "local_ip", "mac_addresses", ... },
    "storage": { "drive_info": { "total_gb", "used_gb", "free_gb", ... } },
    "memory": { "virtual_memory", "swap_memory" },
    "processor": { "processor", "cpu_percent", "cpu_freq", ... }
  }
  ```

#### `database.py`
- SQLite database management with SQLAlchemy ORM
- Encryption-ready (can be extended with sqlcipher3)
- Database tables:
  - `user` - User accounts and credentials and stored device information
  - `applicationLogs` - Monitored applications
  - `keystrokeSummary` - Keystroke activity logs
  - `activityLog` - User activity events
  - `alertLogs` - Security alerts
  - `monitoringSettings` - User preferences
  - And more...

#### `keylogger.py`
- Real-time keyboard event monitoring
- Tracks keystroke frequency and patterns
- Stores data for periodic analysis
- Thread-safe operations

## Usage

### First Run

On first run, the application will:

1. **Request Admin Privileges**
   - If not running as admin, UAC prompt appears
   - You must click "Yes" to grant permissions
   - Application restarts with elevated privileges

2. **Initialize Database**
   - Creates SQLite database file (`spyglass.db`)
   - Sets up schema with all necessary tables
   - Enables WAL (Write-Ahead Logging) for better performance

3. **Gather Device Information**
   - Runs system diagnostic to gather device details
   - Displays summary of retrieved information
   - Stores all data in database for future reference

### Main Menu

```
==================================================
SPYGLASS MONITORING APPLICATION
==================================================
1. Start Monitoring       - Begin keystroke logging
2. Stop Monitoring        - Halt keystroke logging
3. Show Analytics         - View statistics (TBD)
4. Show Reports           - Generate monitoring reports
5. Settings               - Display stored device information & config setup
6. Exit                   - Close application
==================================================
```

## Database Schema

All device data and monitoring logs are stored in `spyglass.db` with the following key tables:

### userInfo Table
Stores the retrieved device information from initialization:
```sql
CREATE TABLE userInfo (
  userID TEXT PRIMARY, --machineId
  SystemInfo  --osType,  osVersion,  osBuild 
  username TEXT, --hostname
  processorCount INTEGER,
  macAddresses TEXT (JSON), 
  systemInfo TEXT (JSON),
  createdAt TIMESTAMP
);
```

## Security Considerations

- Admin privileges are required to access certain system information
- Database file is created in the application directory
- For production use, consider:
  - Encrypting the database file using SQLCipher
  - Using environment variables for sensitive config
  - Implementing proper access controls
  - Securing the device machine ID

## Extending the Application

### Adding New Device Info

Edit `userInfo.py` to add new information gathering methods:

```python
def get_custom_info(self) -> Dict[str, Any]:
    # Get custom device information# 
    try:
        # Your custom information gathering code
        return {"custom_key": "value"}
    except Exception as e:
        print(f"Error: {e}")
        return {}
```

Then add it to the `gather_info()` method in the `__init__` function.

### Enabling Database Encryption

To use SQLCipher for encrypted databases:

1. Install sqlcipher3:
   ```bash
   pip install sqlcipher3
   ```

2. Update database.py to use sqlcipher3 instead of sqlite3

3. Uncomment the PRAGMA statements in the database schema

## Troubleshooting

### Admin Privileges Error
**Problem**: "This application requires administrator privileges"
**Solution**: 
- Run Command Prompt as Administrator
- Run the script: `python main.py`
- Click "Yes" on UAC prompt

### Database Lock Error
**Problem**: "database is locked"
**Solution**:
- Close all instances of the application
- Delete `spyglass.db` to reset (will lose data)
- Run application again

### Import Errors
**Problem**: "ModuleNotFoundError: No module named 'X'"
**Solution**:
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify you're using the correct Python version (3.8+)

### Keystroke Monitoring Not Working
**Problem**: Keystrokes not being logged
**Solution**:
- Ensure application is running with admin privileges
- Try restarting the application
- Check Windows permissions for Python

## License

[Add your license information here]

## Author

[Kelechi Ariwodo]

## Version

0.0.3 - Initial Release
