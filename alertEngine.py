import psutil
import ctypes
import threading
import logging
import tkinter as tk
from datetime import datetime
from typing import Optional
from db.database import (
    insertIntoActivityLogTable,
    insertIntoAlertTable,
    updateAlertResponse,
    getOrCreateAppID,
)

SCRIPTS_EXT = {'.exe', '.bat', '.cmd', '.ps1', '.vbs', '.js', '.py', '.gs', '.wsf'}

BLOCKLISTED_APPS = {
    #spyglass
    'spyglass.exe', 'spyglass.py',

    # remote access tools
    'teamviewer.exe', 'anydesk.exe', 'logmein.exe', 'ultraviewer.exe', 'ammyy.exe',

    #network sniffers
    'wireshark.exe', 'tcpdump.exe', 'nmap.exe', 'fiddler.exe', 'netsh.exe',

    #Credential harvesting
    'mimikatz.exe', 'hashcat.exe', 'john.exe', 'hydra.exe', 'crunch.exe', 'lazagne.exe',

    #Reverseshells
    'nc.exe', 'netcat.exe', 'ncat.exe', 'socat.exe', 'plink.exe', 'msfvenom.exe',
}

PASSWORD_KEYS = {'password', 'pass', 'sign in', 'login', 'auth', 'credentials', 'authentication'}

LOW_SECURITY = 'low'
MED_SECURITY = 'medium'
HIGH_SECURITY = 'high'
CRITICAL_SECURITY = 'critical'

SEVERITY_TO_LOG_LEVEL = {
    'low': logging.INFO,
    'medium': logging.WARNING,
    'high': logging.ERROR,
    'critical': logging.CRITICAL,
}

SEVERITY_COLOURS = {
    'low': "#2d6a4f",       # dark green
    'medium': "#e76f51",    # orange
    'high': "#d62828",      # red
    'critical': "#6a040e",  # dark red
}


class AlertEngine:
    def __init__(self, user_id: str, user_thresholds: dict = None):
        self.user_id = user_id
        self.is_running = False
        self.baseline_pids = set()
        self.alert_history = {}
        self.scan_thread = None
        self.lock = threading.Lock()
        self.polling_interval = 15  # seconds

        # Keystroke subscription
        self.keystroke_monitor = None
        self.last_keystroke_snapshot = {}
        self.last_snapshot_time = None

        # Dynamic thresholds from user input
        self._apply_thresholds(user_thresholds or {})

    # Default severity-level thresholds
    DEFAULT_THRESHOLDS = {
        'cpu_limit': {'low': 30, 'medium': 55, 'high': 70, 'critical': 90},
        'memory_limit': {'low': 40, 'medium': 65, 'high': 75, 'critical': 90},
        'process_activity': {'low': 20, 'medium': 50, 'high': 100, 'critical': 200},
        'same_script_limit': {'low': 10,  'medium': 20, 'high': 50,  'critical': 100},
        'keystroke_frequency': {'low': 40, 'medium': 60, 'high': 100, 'critical': 120},
        'modifier_key_threshold': {'low': 10,  'medium': 25,  'high': 50,  'critical': 75},
    }

    SEVERITY_ORDER = [('critical', CRITICAL_SECURITY), ('high', HIGH_SECURITY),
                      ('medium', MED_SECURITY), ('low', LOW_SECURITY)]

    def _apply_thresholds(self, t: dict) -> None:
        """Extract threshold dicts (each with low/medium/high/critical keys)."""
        self.thresholds = {}
        for name, defaults in self.DEFAULT_THRESHOLDS.items():
            user_val = t.get(name, {})
            if isinstance(user_val, dict):
                self.thresholds[name] = {
                    sev: int(user_val.get(sev, defaults[sev]))
                    for sev in ('low', 'medium', 'high', 'critical')
                }
            else:
                # Backward compat: single value → treat as high threshold
                self.thresholds[name] = dict(defaults)
                if user_val is not None:
                    self.thresholds[name]['high'] = int(user_val)

    def _check_severity(self, value: float, threshold_name: str, alert_type: str,
                        key_prefix: str, message_template: str,
                        app_name=None, exe_path=None):
        """Check a value against all 4 severity levels (highest first) and raise one alert."""
        levels = self.thresholds.get(threshold_name, {})
        for sev_key, sev_const in self.SEVERITY_ORDER:
            limit = levels.get(sev_key)
            if limit is not None and value >= limit:
                self.raise_alert(
                    sev_const,
                    alert_type=alert_type,
                    key=f"{key_prefix}_{sev_key}",
                    message=message_template.format(value=value, severity=sev_key.upper(), limit=limit),
                    app_name=app_name, exe_path=exe_path)
                break  # only fire the highest matched severity

    def update_thresholds(self, new_thresholds: dict) -> None:
        """Hot-reload thresholds without restart."""
        self._apply_thresholds(new_thresholds)
        with self.lock:
            self.alert_history.clear()  # reset dedup so new limits can fire
        logging.info(f"AlertEngine thresholds updated: {new_thresholds}")

    def subscribe_to_keylogger(self, keystroke_monitor) -> None:
        """Subscribe to live KeystrokeMonitor for keystroke threshold checks."""
        self.keystroke_monitor = keystroke_monitor
        self.last_keystroke_snapshot = {}
        self.last_snapshot_time = datetime.now()
        logging.info("AlertEngine subscribed to keystroke monitor")

    def start(self):
        if self.is_running:
            logging.warning("Alert Engine is already running.")
            return
        logging.info("Setting up Alert Engine with baseline snapshot...")
        self.baseline_pids = {p.pid for p in psutil.process_iter()}
        self.is_running = True
        self.scan_thread = threading.Thread(target=self.scan_loop, daemon=True)
        self.scan_thread.start()

    def stop(self):
        if not self.is_running:
            logging.warning("Alert Engine is not running.")
            return
        logging.info("Stopping Alert Engine...")
        self.is_running = False

    def scan_loop(self):
        #runs checks each polling interval
        while self.is_running:
            self.check_thresholds()
            threading.Event().wait(self.polling_interval)

    # ── threshold checks ──────────────────────────────────────────

    def check_thresholds(self):
        scripts = self.get_running_scripts()
        new_scripts = [s for s in scripts if s['pid'] not in self.baseline_pids]

        #LOW - NON SYSTEM SCRIPTS
        for script in new_scripts:
            self.raise_alert(
                LOW_SECURITY,
                alert_type="Background Script",
                key=f"bg_{script['pid']}",
                message=f"Background script detected: {script['name']} (PID {script['pid']})",
                app_name=script['name'], exe_path=script.get('exe', ''))

        # Process activity threshold (simultaneous scripts) — 4 severity levels
        self._check_severity(
            value=len(scripts),
            threshold_name='process_activity',
            alert_type="Excessive Scripts",
            key_prefix="script_volume",
            message_template="Scripts ({value}) exceeded {severity} threshold ({limit})")

        # Same-app script flood — 4 severity levels
        app_counts = {}
        for script in scripts:
            app_counts.setdefault(script['name'], []).append(script)
        for app, instances in app_counts.items():
            self._check_severity(
                value=len(instances),
                threshold_name='same_script_limit',
                alert_type="Suspicious App Behavior",
                key_prefix=f"AppFlood_{app}",
                message_template=f"{{value}} scripts from {app} ({{severity}} limit: {{limit}})",
                app_name=app, exe_path=instances[0].get('exe', ''))

        #CRITICAL - BLOCKLISTED APPS
        for script in scripts:
            if script['name'].lower() in BLOCKLISTED_APPS:
                if script['name'].lower() in {'spyglass.exe', 'spyglass.py'}:
                    msg = f"SPYGLASS is now watching your device"
                else:
                    msg = f"Blocklisted app detected: {script['name']} (PID {script['pid']})"
                self.raise_alert(
                    CRITICAL_SECURITY,
                    alert_type="Blocklisted App Detected",
                    key=f"Blocklist_{script['name']}",
                    message=msg,
                    app_name=script['name'], exe_path=script.get('exe', ''))

        #CRITICAL - password fields detected
        for title in self.get_all_window_titles():
            if any(key in title.lower() for key in PASSWORD_KEYS):
                self.raise_alert(
                    CRITICAL_SECURITY,
                    alert_type="Password Field Detected",
                    key=f"PasswordField_{title[:40]}",
                    message=f'Potential password field in window: "{title}"',
                    app_name=None, exe_path=None)
                break

        # CPU threshold — 4 severity levels
        cpu_percent = psutil.cpu_percent(interval=0)
        self._check_severity(
            value=cpu_percent,
            threshold_name='cpu_limit',
            alert_type="CPU Threshold Exceeded",
            key_prefix="cpu_limit",
            message_template="CPU usage {value:.1f}% exceeded {severity} threshold ({limit}%)")

        # Memory threshold — 4 severity levels
        mem = psutil.virtual_memory()
        self._check_severity(
            value=mem.percent,
            threshold_name='memory_limit',
            alert_type="Memory Threshold Exceeded",
            key_prefix="memory_limit",
            message_template="Memory usage {value:.1f}% exceeded {severity} threshold ({limit}%)")

        # Keystroke thresholds (subscribed to keylogger)
        self._check_keystroke_thresholds()

    def _check_keystroke_thresholds(self):
        """Check keystroke frequency and modifier combo thresholds via keylogger subscription."""
        if not self.keystroke_monitor:
            return

        now = datetime.now()
        with self.keystroke_monitor.lock:
            current_snapshot = self.keystroke_monitor.keystrokes.copy()

        # Calculate elapsed time since last snapshot
        if self.last_snapshot_time:
            elapsed_minutes = max((now - self.last_snapshot_time).total_seconds() / 60.0, 0.01)
        else:
            elapsed_minutes = self.polling_interval / 60.0

        # Delta keystrokes since last check
        modifier_keys = {'Key.shift', 'Key.shift_r', 'Key.ctrl_l', 'Key.ctrl_r',
                         'Key.alt_l', 'Key.alt_r', 'Key.cmd', 'Key.cmd_r'}
        delta_total = 0
        delta_modifiers = 0

        for key, count in current_snapshot.items():
            prev = self.last_keystroke_snapshot.get(key, 0)
            delta = count - prev
            if delta > 0:
                delta_total += delta
                if key in modifier_keys:
                    delta_modifiers += delta

        keys_per_minute = delta_total / elapsed_minutes

        # Keystroke frequency — 4 severity levels
        self._check_severity(
            value=keys_per_minute,
            threshold_name='keystroke_frequency',
            alert_type="Keystroke Frequency Exceeded",
            key_prefix="keystroke_freq",
            message_template="Typing speed {value:.0f} KPM exceeded {severity} threshold ({limit})")

        # Modifier combo — 4 severity levels
        self._check_severity(
            value=delta_modifiers,
            threshold_name='modifier_key_threshold',
            alert_type="Modifier Key Threshold Exceeded",
            key_prefix="modifier_combo",
            message_template="Modifier combos ({value}) exceeded {severity} threshold ({limit})")

        # Update snapshot for next interval
        self.last_keystroke_snapshot = current_snapshot
        self.last_snapshot_time = now

    # ── alert dispatcher ──────────────────────────────────────────
    def raise_alert(self, severity: str, alert_type: str, key: str, message: str,
                    app_name: Optional[str] = None, exe_path: Optional[str] = None):
        #Log alert, update DB, show popup
        alert_key = (severity, key)
        if alert_key in self.alert_history:
            return
        self.alert_history[alert_key] = datetime.now()

        log_level = SEVERITY_TO_LOG_LEVEL.get(severity, logging.WARNING)
        logging.getLogger('app').log(log_level, f"[{severity.upper()}] {message}")

        # update DB
        app_id = None
        if app_name and exe_path:
            app_id = getOrCreateAppID(app_name, exe_path)
        alert_id = insertIntoAlertTable(
            userID=self.user_id, alertType=alert_type,
            severity=severity, message=message, appID=app_id)
        if app_id is not None:
            insertIntoActivityLogTable(
                self.user_id, appID=app_id,
                action=f"alert_{alert_type}", category=severity, reason=message)

        # Show popup on a separate thread
        threading.Thread(
            target=self.show_popup,
            args=(severity, message, key, alert_id),
            daemon=True).start()

    # ── Tkinter popup ─────────────────────────────────────────────

    def show_popup(self, severity: str, message: str, key: str,
                   alert_id: Optional[int] = None):
        bg = SEVERITY_COLOURS.get(severity, '#000')
        popup_w, popup_h = 380, 120
        root = tk.Tk()
        root.title(f"SPYGLASS ALERT")
        root.configure(bg=bg)
        root.overrideredirect(True)          # borderless window
        root.attributes("-topmost", True)
        screen_w = root.winfo_screenwidth()
        root.geometry(f"{popup_w}x{popup_h}+{screen_w - popup_w - 75}+20")
        root.resizable(False, False)

        # ── title ──
        tk.Label(root, text=f"SPYGLASS ALERT ({severity.upper()})",
                 font=("Gruppo", 9, "bold"),
                 bg=bg, fg="#ffffff", anchor='w').pack(fill='x', padx=10, pady=(8, 0))

        # ── message ──
        tk.Label(root, text=message.upper(),
                 font=("Gruppo", 8, "bold"),
                 bg=bg, fg="#ffffff",
                 wraplength=355, justify='left', anchor='nw').pack(fill='both', expand=True, padx=10, pady=(4, 0))

        # ── button bar ──
        btn_frame = tk.Frame(root, bg=bg)
        btn_frame.pack(fill='x', side='bottom')

        def dismiss():
            if alert_id is not None:
                updateAlertResponse(alert_id, 'dismissed')
            root.destroy()

        def resolve():
            if alert_id is not None:
                updateAlertResponse(alert_id, 'resolved')
            with self.lock:
                self.alert_history.pop((severity, key), None)
            root.destroy()

        btn_style = dict(font=("Gruppo", 8, "bold"), fg="#ffffff",
                         relief='flat', cursor='hand2', pady=4)
        tk.Button(btn_frame, text="DISMISS", command=dismiss,
                  bg="#dad8d8", activebackground="#3e5a6a",
                  **btn_style).pack(side='left', fill='x', expand=True)
        tk.Button(btn_frame, text="RESOLVE", command=resolve,
                  bg="#50B17C", activebackground="#3e5a6a",
                  **btn_style).pack(side='left', fill='x', expand=True)

        root.after(30000, root.destroy)  # auto-close after 30s
        root.mainloop()

    # ── helpers ────────────────────────────────────────────────────

    def get_running_scripts(self):
        scripts = []
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                info = proc.info
                name = (info.get('name') or '').lower()
                if any(name.endswith(ext) for ext in SCRIPTS_EXT):
                    scripts.append({
                        'pid': info['pid'],
                        'name': info.get('name', ''),
                        'exe': info.get('exe') or '',
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return scripts

    def get_all_window_titles(self):
        titles = []
        if not hasattr(ctypes, 'windll'):
            return titles

        def enum_cb(hwnd, _):
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                if buf.value:
                    titles.append(buf.value)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        ctypes.windll.user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        return titles
        