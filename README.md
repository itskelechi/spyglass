# Spyglass - Device Monitoring & Keystroke Logger

A comprehensive Windows device monitoring application that captures device information, monitors keystroke activity, and stores encrypted data in a local SQLite database.

## Features

- **Windows Admin Privileges**: Automatically requests and verifies administrator privileges on startup
- **Device Information Retrieval**: Captures comprehensive system information including:
  - OS version, build number, hostname, username
  - CPU/Processor information and count
  - Memory (RAM) specifications
  - Storage information for all disks
  - Network configuration and IP addresses
  - MAC addresses
  
- **Encrypted Database**: Local SQLite database for storing device and monitoring data
- **Keystroke Monitoring**: Real-time keystroke logging and analysis
- **Activity Logging**: Track application usage and user activity
- **Multi-threaded Architecture**: Handles multiple monitoring tasks simultaneously

## System Requirements

- **OS**: Windows (Windows 7 or later)
- **Python**: Python 3.8 or higher
- **Privileges**: Administrator privileges required

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required Packages**:
- `sqlalchemy` - Database ORM
- `psutil` - System and process utilities
- `pynput` - Keyboard monitoring
- `cryptography` - Encryption support

### 2. Run the Application

```bash
python main.py
```

**IMPORTANT**: The application will automatically request Windows administrator privileges if not already running as admin. Click "Yes" on the UAC prompt when it appears.

## Application Structure

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

#### `admin_handler.py`
- Checks current administrator status
- Handles UAC elevation requests
- Verifies admin privileges before allowing sensitive operations

#### `device_info.py`
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
  - `user` - User accounts and credentials
  - `device_info` - Stored device information
  - `application` - Monitored applications
  - `keystroke_summary` - Keystroke activity logs
  - `activity_log` - User activity events
  - `alert` - Security alerts
  - `monitoring_settings` - User preferences
  - And more...

#### `keystroke_monitor.py`
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
5. Show Device Info       - Display stored device information
6. Exit                   - Close application
==================================================
```

## Database Schema

All device data and monitoring logs are stored in `spyglass.db` with the following key tables:

### device_info Table
Stores the retrieved device information from initialization:
```sql
CREATE TABLE device_info (
  deviceInfoID INTEGER PRIMARY KEY,
  userID INTEGER,
  osType TEXT,
  osVersion TEXT,
  osBuild TEXT,
  hostname TEXT,
  username TEXT,
  machineId TEXT UNIQUE,
  processorCount INTEGER,
  totalRamGB REAL,
  localIp TEXT,
  macAddresses TEXT (JSON),
  storageInfo TEXT (JSON),
  systemInfo TEXT (JSON),
  retrievedAt TIMESTAMP
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

Edit `device_info.py` to add new information gathering methods:

```python
def _get_custom_info(self) -> Dict[str, Any]:
    """Get custom device information"""
    try:
        # Your custom information gathering code
        return {"custom_key": "value"}
    except Exception as e:
        print(f"Error: {e}")
        return {}
```

Then add it to the `_gather_info()` method in the `__init__` function.

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

[Add author information here]

## Version

0.1.0 - Initial Release