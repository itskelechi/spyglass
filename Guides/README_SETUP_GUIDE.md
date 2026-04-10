<p align="center">
  <img src="../logo/spyglass_logo.png" alt="Spyglass Logo" width="150" />
  <h1>SPYGLASS</h1>
</p>

### Setup & User Guide

---

## Table of Contents

1. [What Is Spyglass?](#1-what-is-spyglass)
2. [Key Functionalities](#2-key-functionalities)
3. [Installation & Running](#3-installation--running)
4. [Terminal Mode vs GUI Mode](#4-terminal-mode-vs-gui-mode)
5. [Configuration & Threshold Advice](#5-configuration--threshold-advice)
6. [Resetting the Database](#6-resetting-the-database)
7. [Pip Requirements](#7-pip-requirements)
8. [Files Created at Runtime](#8-files-created-at-runtime)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. What Is Spyglass?

Spyglass is a **Windows endpoint-monitoring application** that tracks system activity in real time — CPU/memory usage, running processes, installed applications, and (optionally) keystroke patterns. It stores everything in a locally encrypted SQLCipher database, evaluates configurable thresholds, and raises severity-based alerts when anomalies are detected.

The app can run entirely in the **terminal** or through a **PyQt6 GUI** with a dashboard, analytics, and report views.

---

## 2. Key Functionalities

### 2.1 Admin Privilege Verification (`adminHandler.py`)
- Checks if the process is running with Windows Administrator rights via the Windows API (`ctypes.windll.shell32.IsUserAnAdmin`).
- If not elevated, prompts the user and re-launches the process with `runas`.
- Administrator rights are **required** — monitoring system processes, reading the Windows registry, and capturing keystrokes all need elevated permissions.

### 2.2 User Consent & Monitoring Level (`consent.py` / GUI `consent_window.py`)
- Displays a full disclosure of what Spyglass monitors **before** monitoring begins.
- The user selects a monitoring level:
  | Level | What It Monitors |
  |-------|-----------------|
  | **LOW** | CPU, memory, running processes, installed apps, foreground window tracking |
  | **HIGH** | Everything in LOW **plus** keystroke frequency analysis and modifier-key combination detection |
- No data is collected until the user explicitly consents.

### 2.3 Threshold Configuration (`threshold_window.py` / `consent.py`)
- After choosing a monitoring level the user can set alert thresholds at **four severity tiers**: 
   Low, Medium, High, and Critical 
or defer to system defaults.
- **Basic thresholds** (both LOW and HIGH modes):

  | Threshold | What It Measures | Default (Low → Critical) |
  |-----------|-----------------|--------------------------|
  | CPU Usage | Sustained processor load (%) | 30 / 55 / 70 / 90 |
  | Memory Usage | RAM utilization (%) | 40 / 65 / 75 / 90 |
  | Process Activity | Number of active script processes | 20 / 50 / 100 / 200 |
  | Same-App Script Limit | Duplicate instances of one app | 10 / 20 / 50 / 100 |

- **Advanced thresholds** (HIGH mode only):

  | Threshold | What It Measures | Default (Low → Critical) |
  |-----------|-----------------|--------------------------|
  | Keystroke Frequency | Keys per minute | 40 / 60 / 100 / 120 |
  | Modifier Key Combos | Ctrl/Alt/Shift combos per interval | 10 / 25 / 50 / 75 |

### 2.4 Application Monitoring (`appMonitor.py`)
- Runs on a **daemon thread** polling every 15 seconds.
- **Foreground window tracking** — logs the currently active window (process name, PID, executable path, window title).
- **Running process enumeration** — iterates all system processes via `psutil` and collects name, PID, memory, and CPU usage.
- **Installed application scanning** — reads the Windows Registry `Uninstall` keys (both `HKEY_LOCAL_MACHINE` and `HKEY_CURRENT_USER`) to builds a full software inventory, then batch-inserts into the database.

### 2.5 Keystroke Monitoring (`keystroke_monitor.py` / `keylogger.py`)
- Only active when the user selects **HIGH** monitoring.
- Uses `pynput` to listen for key-press events in a background thread.
- Records **aggregate counts per key** (e.g. `'e': 42`), **not raw input streams** —
  passwords and messages are never stored verbatim.
- `keylogger.py` wraps the monitor with start/stop control, calculates
  keys-per-minute, and writes a summary row to the database.

### 2.6 Alert Engine (`alertEngine.py`)
- Daemon thread that runs `check_thresholds()` every **15 seconds**.
- Compares live system metrics against the user's configured thresholds.
- Detects:
  - CPU / memory threshold breaches
  - Excessive background script processes
  - Blocklisted applications (TeamViewer, AnyDesk, Wireshark, Mimikatz, netcat, and 16 others)
  - Suspicious keystroke patterns (HIGH mode) — abnormal typing speed or modifier-key storms
  - Password-field typing patterns (keywords like "password", "login", "sign in")
- Each alert is assigned a severity (**low / medium / high / critical**), logged to the database, and surfaced as a popup (Tkinter in terminal mode, Qt signal in GUI mode).

### 2.7 Encrypted Database (`database.py`)
- All monitoring data is stored locally in `spyglass.db` (project root).
- Encrypted with **SQLCipher**.
- 13 tables including: `user`, `application`, `monitoring_settings`, `threshold`, `activity_log`, `keystroke_summary`, `alert`, `report`, and more.
- Multi-thread safe (`check_same_thread=False`).

### 2.8 System Information Collection (`userInfo.py`)
- Gathers a comprehensive device profile on first run:
  OS version, hostname, username, machine ID, processor details, RAM, storage partitions, network interfaces, MAC addresses, and Windows build information.
- Saved to `system_info.json` and inserted into the `user` table.

### 2.9 Configuration Persistence (`configSettings.py`)
- Active settings are stored in `spyglass_settings.json`.
- Tracks monitoring level, which features are enabled, thresholds, alert interval, and storage limits.
- Settings can also be defined in `config.ini` for advanced users (database paths,  encryption toggles, screenshot intervals, debug logging, auto-backup).

---

## 3. Installation & Running

### Prerequisites
- **Windows 10/11** (required for registry scanning and admin elevation)
- **Python 3.10+** (3.11 or 3.12 recommended)
- **Administrator privileges** (right-click terminal → "Run as administrator")

### Step 1 — Clone or Download the Project

Place the `spyglass` folder anywhere you like. Open a terminal and `cd` into it:

```powershell
cd "C:\path\to\spyglass"
```

### Step 2 — Create a Virtual Environment (recommended)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3 — Install Dependencies

```powershell
pip install -r requirements.txt
```

If you get permission errors:
```powershell
pip install --user -r requirements.txt
```

### Step 4 — Run the Application

**Option A — Interactive launcher (recommended):**
```powershell
python main.py
```
You will see a menu:
```
[1] Launch with Graphic Interface
[2] Launch in Terminal
[3] Exit
```

**Option B — Direct flags:**
```powershell
python main.py --gui     # Launch the PyQt6 GUI directly
python main.py --cli     # Launch in terminal mode directly
```

**Option C — Entry-point scripts:**
```powershell
python spyglassGUI.py    # GUI only
python spyglass.py       # Terminal only
```

### Step 5 — Follow the Prompts

1. **Admin elevation** — Accept the prompt when it appears.
2. **Consent screen** — Read the disclosure, select LOW or HIGH.
3. **Threshold configuration** — Adjust values or accept the defaults.
4. **Monitoring begins** — The dashboard (GUI) or menu (terminal) appears.

---

## 4. Terminal Mode vs GUI Mode

| Feature | Terminal Mode | GUI Mode |
|---------|-------------|----------|
| Entry point | `python spyglass.py` or `main.py --cli` | `python spyglassGUI.py` or `main.py --gui` |
| Consent/thresholds | Text prompts in the console | glass inspired dialog windows |
| Dashboard | Text menu with numbered options | 3-page dashboard (Home, Analytics, Reports) |
| Alerts | Tkinter popup windows (30 s auto-close) | Qt signal-driven notifications in the GUI |
| Real-time stats | Print to console on demand | Live-updating stat cards and tables |
| Reports | Console output / log files | Sortable table view with export |
| Best for | Headless servers, SSH sessions, quick tests | Day-to-day use, visual monitoring |

Both modes use the **same core engine** (`Spyglass`, `AlertEngine`, `AppMonitor`,
`KeystrokeMonitor`, `DatabaseManager`). The only difference is how information is
presented and how user input is collected.

You can switch freely — data written by one mode is readable by the other because
they share the same encrypted database.

---

## 5. Configuration & Threshold Advice

### How Thresholds Work

Each threshold has **four severity levels**. When a metric crosses a level, an
alert of that severity is raised:

| Severity | Meaning | Colour |
|----------|---------|--------|
| Low | Informational — something to note | Teal |
| Medium | Warning — worth investigating | Yellow |
| High | Elevated — likely needs attention | Orange |
| Critical | Urgent — immediate action recommended | Red |

### Recommended Profiles

#### 🎮 Gamer
Games regularly push CPU and memory hard. Raising these limits prevents false
alerts during normal gaming sessions.

| Threshold | Low | Medium | High | Critical |
|-----------|-----|--------|------|----------|
| CPU Usage (%) | 80 | 90 | 95 | 99 |
| Memory Usage (%) | 75 | 85 | 92 | 98 |
| Process Activity | 30 | 70 | 150 | 250 |
| Same-App Script Limit | 5 | 15 | 30 | 60 |

#### ⌨️ Fast Typist / Programmer
If you type at 80+ WPM, the default keystroke thresholds will trigger constantly.
Raise keystroke frequency and modifier-key limits to match your style.

| Threshold | Low | Medium | High | Critical |
|-----------|-----|--------|------|----------|
| Keystroke Frequency (keys/min) | 400 | 600 | 800 | 1000 |
| Modifier Key Combos | 30 | 60 | 100 | 150 |
| CPU Usage (%) | 60 | 75 | 90 | 95 |
| Memory Usage (%) | 60 | 75 | 85 | 95 |

#### 🖥️ General Office / Student
The defaults work well for most office and school workloads. No changes needed
unless you notice false alerts.

| Threshold | Low | Medium | High | Critical |
|-----------|-----|--------|------|----------|
| CPU Usage (%) | 60 | 75 | 90 | 95 |
| Memory Usage (%) | 60 | 75 | 85 | 95 |
| Process Activity | 20 | 50 | 100 | 200 |
| Same-App Script Limit | 5 | 10 | 20 | 50 |

#### 🔒 Security-Focused / IT Admin
Tighter thresholds catch anomalies sooner. Use HIGH monitoring with low
keystroke limits to flag unusual input patterns quickly.

| Threshold | Low | Medium | High | Critical |
|-----------|-----|--------|------|----------|
| CPU Usage (%) | 50 | 65 | 80 | 90 |
| Memory Usage (%) | 50 | 65 | 80 | 90 |
| Process Activity | 10 | 30 | 60 | 100 |
| Same-App Script Limit | 3 | 7 | 15 | 30 |
| Keystroke Frequency | 150 | 250 | 400 | 600 |
| Modifier Key Combos | 8 | 20 | 40 | 80 |

### Changing Thresholds After Setup

- **GUI**: Open the Reports page → click **Settings** → a threshold dialog appears.
- **Terminal**: Edit `spyglass_settings.json` directly — the `"thresholds"` key
  contains all six threshold types, each with `low`, `medium`, `high`, `critical`
  sub-keys.
- Changes take effect the next time the alert engine's scan loop runs (≤ 15 s).

---

## 6. Resetting the Database

If you encounter errors like **"file is not a database"**, **"database is locked"**,
or **"no such table"**, the cleanest fix is to delete the database and let Spyglass
recreate it on the next run.

### PowerShell (Run as Administrator)

```powershell
# 1. Kill any running Python/Spyglass processes
taskkill /IM python.exe /F

# 2. Navigate to the project folder
cd "C:\path\to\spyglass"

# 3. Force-remove the database and its WAL/SHM journal files
Remove-Item "spyglass.db*" -Force

# 4. (Optional) Also remove the settings file for a full reset
Remove-Item "spyglass_settings.json" -Force

# 5. Restart the application — the database will be recreated automatically
python main.py
```

### Command Prompt (Run as Administrator)

```cmd
taskkill /IM python.exe /F
cd "C:\path\to\spyglass"
del /F /Q spyglass.db*
python main.py
```

### Why This Happens

The database is **encrypted with SQLCipher**. Common causes of corruption:

- The `.db` file was created with a different encryption key (e.g. an older
  version of the code used a different key string).
- The process was killed mid-write and the WAL journal is inconsistent.
- The file was opened by another tool (DB Browser, VS Code extension) that
  does not support SQLCipher, corrupting the header.
- Multiple Spyglass instances wrote to the file simultaneously.

Deleting `spyglass.db` is safe — Spyglass recreates the full schema on startup.
You will lose historical monitoring data, but all configuration is preserved in
`spyglass_settings.json`.

---

## 7. Pip Requirements

All dependencies are listed in `requirements.txt`:

| Package | Version | Purpose |
|---------|---------|---------|
| `sqlalchemy` | 2.0.23 | Database ORM (used alongside raw SQL) |
| `psutil` | 5.9.6 | CPU, memory, process, and disk metrics |
| `pynput` | 1.7.6 | Keyboard and mouse event capture |
| `cryptography` | 41.0.7 | General-purpose encryption utilities |
| `sqlcipher3-binary` | 3.46.1 | SQLCipher bindings for encrypted SQLite |
| `pywin32` | 306 | Windows API access (services, registry) |
| `PyQt6` | ≥ 6.6.0 | GUI framework (only needed for GUI mode) |

Install everything at once:

```powershell
pip install -r requirements.txt
```

If you only plan to use **terminal mode**, you can skip PyQt6:

```powershell
pip install sqlalchemy psutil pynput cryptography sqlcipher3-binary pywin32
```

---

## 8. Files Created at Runtime

| File | Description |
|------|------------|
| `spyglass.db` | SQLCipher-encrypted database — all monitoring data |
| `spyglass.db-wal` / `spyglass.db-shm` | Write-ahead log and shared memory (auto-managed) |
| `spyglass_settings.json` | Active configuration (monitoring level, thresholds, toggles) |
| `system_info.json` | Device profile snapshot captured at first run |
| `Reports/spyglass_*.log` | Timestamped log files (one per session) |

---

## 9. Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'X'` | Run `pip install -r requirements.txt` |
| `This application requires administrator privileges` | Right-click your terminal → **Run as administrator** |
| `file is not a database` | See [Section 6 — Resetting the Database](#6-resetting-the-database) |
| `Database is locked` / `no such table` | Kill all Python processes, delete `spyglass.db*`, restart |
| Keystroke test not capturing anything | Make sure you selected **HIGH** monitoring level |
| UAC prompt never appears | Launch the terminal as admin first, then run the app |
| PyQt6 import errors in your editor | Your IDE may not be using the venv interpreter — select `.venv/Scripts/python.exe` as the Python path |
| `pip install PyQt6` fails | Upgrade pip first: `python -m pip install --upgrade pip` |

---

## Important Security Notes

- In **HIGH** mode Spyglass captures aggregate keystroke counts — this includes
  keystrokes typed into password fields, emails, and chat windows.
- All data is encrypted at rest with SQLCipher (AES-256).
- Data never leaves the local machine.
- Only run Spyglass on devices you own or have explicit authorization to monitor.
- Keep the project folder permissions restricted to your user account.

**This software is intended for authorized endpoint monitoring and security
research only.**
