import logging
import os
import sqlite3
from pathlib import Path
from typing import Optional

from userInfo import UserInfo

# Import sqlcipher3 as sqlite3 replacement for encrypted databases
try:
    import sqlcipher3 as sqlite3
    USING_SQLCIPHER = True
except ImportError:
    import sqlite3
    USING_SQLCIPHER = False
    print("Warning: sqlcipher3 not found. Using standard sqlite3 without encryption.")


class DatabaseManager:
    # Manage Spyglass database
    def __init__(self, db_path: str = "spyglass.db"):
        self.connection: Optional[sqlite3.Connection] = None
        self.db_path = db_path
        self.encryption_key = None
        
    def initializeDB(self, create_tables: bool = True, encryption_key: str = "spyglass_default_key") -> None:
        # Initialize the encrypted database and create tables if needed
        print("Initializing Spyglass database with SQLCipher encryption..." if USING_SQLCIPHER else "Initializing Spyglass database...")
        
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
            self.encryption_key = encryption_key
            
            # Set encryption key and cipher settings for SQLCipher
            if USING_SQLCIPHER:
                cursor = self.connection.cursor()
                cursor.execute(f"PRAGMA key = '{encryption_key}'")
                cursor.execute("PRAGMA cipher_page_size = 4096")
                cursor.execute("PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512")
                cursor.close()
            
            if create_tables:
                self.createAppSchema()
                print("Database initialized and tables created successfully.")
                
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise
                  
    def createAppSchema(self) -> None:
        # Create necessary tables in the database: USER INFO, KEYSTROKE LOGS, EVENT LOGS, ALERTS, SCREENSHOTS
        print("Creating database tables...")
        
        if self.connection is None:
            print("Database connection is not initialized. Cannot create tables.")
            return
        
        try:
            cursor = self.connection.cursor()
            
            # Execute all table creation and index statements
            cursor.executescript("""
                    PRAGMA foreign_keys = ON;
                    PRAGMA synchronous = FULL;
                    PRAGMA temp_store = MEMORY;
                    PRAGMA journal_mode = WAL;
                    PRAGMA query_only = OFF;


                    -- -------------------------
                    -- USER
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS user (
                    userID        TEXT PRIMARY KEY,
                    username      TEXT    NOT NULL,
                    userSystem     TEXT    NOT NULL,
                    processor      TEXT    NOT NULL,
                    createdAt     TEXT    NOT NULL DEFAULT (datetime('now')),

                    CONSTRAINT uq_user_id UNIQUE (userID)
                    );

                    -- -------------------------
                    -- APPLICATION
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS application (
                    appID           INTEGER PRIMARY KEY AUTOINCREMENT,
                    appName         TEXT    NOT NULL,
                    executablePath  TEXT    NOT NULL,
                    vendor           TEXT,

                    CONSTRAINT uq_application_exec_path UNIQUE (executablePath)
                    );

                    -- -------------------------
                    -- MONITORING_SETTINGS
                    -- (one row per user)
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS monitoring_settings (
                    settingsID               INTEGER PRIMARY KEY AUTOINCREMENT,
                    userID                   TEXT NOT NULL,
                    aggressivenessLevel      TEXT    NOT NULL,           -- e.g., low/medium/high
                    screenshotInterval       INTEGER,                    -- seconds/minutes (define in app)
                    keystrokeLoggingEnabled INTEGER NOT NULL DEFAULT 0, -- boolean (0/1)
                    appMonitoringEnabled    INTEGER NOT NULL DEFAULT 1, -- boolean (0/1)
                    maxStorageMB            INTEGER NOT NULL DEFAULT 500,

                    CONSTRAINT fk_settings_user
                        FOREIGN KEY (userID) REFERENCES user(userID)
                        ON DELETE CASCADE ON UPDATE CASCADE,

                    CONSTRAINT uq_settings_user UNIQUE (userID),

                    CONSTRAINT ck_settings_keystroke_bool CHECK (keystrokeLoggingEnabled IN (0,1)),
                    CONSTRAINT ck_settings_appmon_bool    CHECK (appMonitoringEnabled IN (0,1))
                    );

                    -- -------------------------
                    -- THRESHOLD
                    -- (privacy and security thresholds)
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS threshold (
                    thresholdID     INTEGER PRIMARY KEY AUTOINCREMENT,
                    userID          TEXT    NOT NULL,
                    appID           INTEGER,                       -- NULL for system-wide thresholds
                    thresholdType   TEXT    NOT NULL,              -- 'basic' or 'advanced' or 'expert'
                    settingName     TEXT    NOT NULL,
                    settingValue    TEXT    NOT NULL,
                    enabled         INTEGER NOT NULL DEFAULT 1,
                    createdAt       TEXT    NOT NULL DEFAULT (datetime('now')),

                    CONSTRAINT fk_threshold_user
                        FOREIGN KEY (userID) REFERENCES user(userID)
                        ON DELETE CASCADE ON UPDATE CASCADE,

                    CONSTRAINT fk_threshold_app
                        FOREIGN KEY (appID) REFERENCES application(appID)
                        ON DELETE CASCADE ON UPDATE CASCADE,

                    CONSTRAINT ck_threshold_enabled CHECK (enabled IN (0,1))
                    );

                    -- -------------------------
                    -- REPORT
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS report (
                    reportID     INTEGER PRIMARY KEY AUTOINCREMENT,
                    userID       TEXT NOT NULL,
                    reportType   TEXT    NOT NULL,     -- e.g., daily_summary, incident_report
                    filePath     TEXT    NOT NULL,
                    generatedAt  TEXT    NOT NULL DEFAULT (datetime('now')),

                    CONSTRAINT fk_report_user
                        FOREIGN KEY (userID) REFERENCES user(userID)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    );

                    -- -------------------------
                    -- ACTIVITY_LOG (Events)
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS activity_log (
                    eventID  INTEGER PRIMARY KEY AUTOINCREMENT,
                    userID      TEXT NOT NULL,
                    appID       INTEGER NOT NULL,
                    timestamp        NOT NULL DEFAULT (datetime('now')),
                    action       TEXT    NOT NULL,      -- e.g., launched, focused, closed
                    category     TEXT,                  -- e.g., productivity, browser, unknown
                    reason       TEXT,                  -- optional justification/explanation
                    duration     INTEGER,               -- seconds

                    CONSTRAINT fk_activity_user
                        FOREIGN KEY (userID) REFERENCES user(userID)
                        ON DELETE CASCADE ON UPDATE CASCADE,

                    CONSTRAINT fk_activity_app
                        FOREIGN KEY (appID) REFERENCES application(appID)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    );

                    -- -------------------------
                    -- KEYSTROKE_SUMMARY
                    -- (metadata summary per event, NOT raw keys)
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS keystroke_summary (
                    keystrokeID     INTEGER PRIMARY KEY AUTOINCREMENT,
                    eventID         INTEGER NOT NULL,
                    intervalStart   TEXT    NOT NULL,
                    intervalEnd     TEXT    NOT NULL,
                    keyCount        INTEGER NOT NULL DEFAULT 0,
                    keysPerMinute   INTEGER,
                    keyCategories   TEXT,            -- e.g., "letters, numbers, backspace"
                    idleSeconds     INTEGER NOT NULL DEFAULT 0,

                    CONSTRAINT fk_keystroke_event
                        FOREIGN KEY (eventID) REFERENCES activity_log(eventID)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    );

                    -- -------------------------
                    -- SCREENSHOT
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS screenshot (
                    screenshotID  INTEGER PRIMARY KEY AUTOINCREMENT,
                    eventID       INTEGER NOT NULL,
                    imagePath     TEXT    NOT NULL,
                    capturedAt    TEXT    NOT NULL DEFAULT (datetime('now')),

                    CONSTRAINT fk_screenshot_event
                        FOREIGN KEY (eventID) REFERENCES activity_log(eventID)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    );

                    -- -------------------------
                    -- VIDEO_RECORDING
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS video_recording (
                    videoID          INTEGER PRIMARY KEY AUTOINCREMENT,
                    eventID          INTEGER NOT NULL,
                    videoPath        TEXT    NOT NULL,
                    durationSeconds  INTEGER NOT NULL DEFAULT 0,

                    CONSTRAINT fk_video_event
                        FOREIGN KEY (eventID) REFERENCES activity_log(eventID)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    );

                    -- -------------------------
                    -- ALERT
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS alert (
                    alertID      INTEGER PRIMARY KEY AUTOINCREMENT,
                    userID       TEXT    NOT NULL,
                    appID        INTEGER,              -- NULL for system-wide alerts
                    severity     TEXT    NOT NULL,      -- low / medium / high / critical
                    alertType    TEXT    NOT NULL,      -- background_script, simultaneous_scripts, etc.
                    message      TEXT    NOT NULL,      -- human-readable description
                    response     TEXT,                  -- NULL = pending, 'dismissed', 'resolved'
                    createdAt    TEXT    NOT NULL DEFAULT (datetime('now')),

                    CONSTRAINT fk_alert_user
                        FOREIGN KEY (userID) REFERENCES user(userID)
                        ON DELETE CASCADE ON UPDATE CASCADE,

                    CONSTRAINT fk_alert_app
                        FOREIGN KEY (appID) REFERENCES application(appID)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    );

                    -- ============================================================
                    -- Indexes (performance)
                    -- ============================================================

                    CREATE INDEX IF NOT EXISTS idx_activity_user_time
                    ON activity_log (userID, timestamp);

                    CREATE INDEX IF NOT EXISTS idx_activity_app_time
                    ON activity_log (appID, timestamp);

                    CREATE INDEX IF NOT EXISTS idx_event_activity_time
                    ON activity_log (eventID, timestamp);

                    CREATE INDEX IF NOT EXISTS idx_alert_severity
                    ON alert (severity);

                    CREATE INDEX IF NOT EXISTS idx_alert_user
                    ON alert (userID);

                    CREATE INDEX IF NOT EXISTS idx_threshold_user
                    ON threshold (userID);

                    CREATE INDEX IF NOT EXISTS idx_threshold_type
                    ON threshold (thresholdType);

                    CREATE INDEX IF NOT EXISTS idx_report_user_time
                    ON report (userID, generatedAt);

                """)
            
            self.connection.commit()
            cursor.close()
            print("Tables created successfully.")
        except Exception as e:
            print(f"Error creating tables: {e}")
            raise
        
    def closeDB(self) -> None:
        # Close the database connection
        if self.connection:
            self.connection.close()
            print("Database connection closed.")
    
    def verifyConnection(self) -> bool:
        # Verify that the database connection is working
        if self.connection is None:
            print("Database connection is not initialized.")
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            print("Database connection verified successfully.")
            return True
        except Exception as e:
            print(f"Database connection verification failed: {e}")
            return False
    
    def insertIntoUserTable(self, deviceInfo: dict) -> bool:
        #Store device information in the user table
        if self.connection is None:
            print("Database connection is not initialized.")
            return False
        try:
            sysInfo = deviceInfo.get('system', {})
            hardwareInfo = deviceInfo.get('hardware', {})
            processorInfo = deviceInfo.get('processor', {})
            
            # Format userSystem as: osType osVersion osBuild
            userSystem = f"{sysInfo.get('os', '')} {sysInfo.get('os_version', '')} (Build {sysInfo.get('os_build', '')})".strip()
            # Use hostname as username
            username = sysInfo.get('hostname', '')
            # Machine ID
            machineID = hardwareInfo.get('machine_id', '')
            #getprocessor info
            processor = processorInfo.get('processor', '')
            # Insert/Update device info into user table
            insert_query = """
                INSERT OR REPLACE INTO user 
                (userID, username,userSystem, processor, createdAt)
                VALUES (?, ?, ?, ?, datetime('now'))
            """
            values = (
                machineID,
                username,
                userSystem,
                processor,
            )            
            cursor = self.connection.cursor()
            cursor.execute(insert_query, values)
            self.connection.commit()
            cursor.close()
            
            print(f"Device information stored successfully for user {machineID}.")
            return True
        except Exception as e:
            print(f"Error storing device information: {e}")
            return False
    
    def displayUserInfo(self, userID: str) -> Optional[dict]:
        """Retrieve device information from the user table"""
        if self.connection is None:
            print("Database connection is not initialized.")
            return None
        
        try:
            import json
            
            query = "SELECT systemInfo FROM user WHERE userID = ? LIMIT 1"
            
            cursor = self.connection.cursor()
            cursor.execute(query, (userID,))
            result = cursor.fetchone()
            cursor.close()
            
            if result and result[0]:
                return json.loads(result[0])
            return None
        except Exception as e:
            print(f"Error retrieving device information: {e}")
            return None

def setDB(db: DatabaseManager) -> None:
    """Register an already-initialised DatabaseManager as the global instance."""
    global spyglassDB
    spyglassDB = db

def getDB() -> DatabaseManager:
    global spyglassDB
    if spyglassDB is None:
        import hashlib
        spyglassDB = DatabaseManager()
        spyglassDB.initializeDB(create_tables=True, encryption_key=hashlib.sha256(b"spyglass_secure_key_v1").hexdigest())
    return spyglassDB

#Insert into tables
def insertIntoAppTable(appName: str, executablePath: str, vendor: Optional[str] = None) -> bool:
    db = getDB()
    if db.connection is None:
        print("Database connection is not initialized. Cannot update schema.")
        return False
    
    print("Updating Application Table in database schema...")
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO application(appName, executablePath, vendor)
            VALUES (?, ?, ?)
            ON CONFLICT(executablePath) DO UPDATE SET
            appName = excluded.appName,
            vendor = excluded.vendor
            """, (appName, executablePath, vendor)
        )
        db.connection.commit()
        cursor.close()
        print("Database schema updated successfully.")
        return True
    except Exception as e:
        print(f"Error updating database schema: {e}")
        return False

def insertIntoMonitoringSettingsTable(userID: str, aggressivenessLevel: str, screenshotInterval: Optional[int] = None,
                                  keystrokeLoggingEnabled: bool = False, appMonitoringEnabled: bool = True,
                                  maxStorageMB: int = 500) -> bool:
    db = getDB()
    if db.connection is None:
        print("Database connection is not initialized. Cannot update schema.")
        return False
    
    print("Updating Monitoring Settings Table in database schema...")
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO monitoring_settings (userID,aggressivenessLevel, screenshotInterval, keystrokeLoggingEnabled, appMonitoringEnabled,maxStorageMB)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(userID) DO UPDATE SET
            aggressivenessLevel = excluded.aggressivenessLevel,
            screenshotInterval = excluded.screenshotInterval,
            keystrokeLoggingEnabled = excluded.keystrokeLoggingEnabled,
            appMonitoringEnabled = excluded.appMonitoringEnabled,
            maxStorageMB = excluded.maxStorageMB
                """, (userID, aggressivenessLevel, screenshotInterval, keystrokeLoggingEnabled, appMonitoringEnabled, maxStorageMB)
        )
        db.connection.commit()
        cursor.close()
        print("Monitoring Settings Table updated successfully.")
        return True
    except Exception as e:
        print(f"Error updating Monitoring Settings Table: {e}")
        return False

def insertIntoThresholdTable(userID: str, thresholdType: str, settingName: str, settingValue: str,
                             appID: Optional[int] = None, enabled: bool = True) -> bool:
    db = getDB()
    if db.connection is None:
        print("Database connection is not initialized. Cannot update schema.")
        return False
    print("Updating Threshold Table in database schema...")
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO threshold (userID, appID, thresholdType, settingName, settingValue, enabled, createdAt)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (userID, appID, thresholdType, settingName, settingValue, int(enabled))
        )
        db.connection.commit()
        cursor.close()
        print("Threshold Table updated successfully.")
        return True
    except Exception as e:
        print(f"Error inserting threshold: {e}")
        return False

def insertDefaultThresholds(userID: str) -> None:
    db = getDB()
    if db.connection is None:
        return
    try:
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM threshold WHERE userID = ? AND thresholdType = 'security'", (userID,))
        count = cursor.fetchone()[0]
        cursor.close()
        if count > 0:
            return  # already seeded
    except Exception:
        return

    defaults = [
        ('security', 'background_script_limit', '1'),
        ('security', 'simultaneous_script_limit', '10'),
        ('security', 'same_script_limit', '3'),
        ('security', 'password_detection', '1'),
        ('security', 'blocklist_enabled', '1'),
    ]
    for t_type, name, value in defaults:
        insertIntoThresholdTable(userID, t_type, name, value)

def getThresholdsForUser(userID: str) -> dict:
    """Load the latest enabled threshold per settingName for a user."""
    db = getDB()
    if db.connection is None:
        return {}
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT settingName, settingValue
            FROM threshold
            WHERE userID = ? AND enabled = 1
              AND thresholdID IN (
                  SELECT MAX(thresholdID) FROM threshold
                  WHERE userID = ? AND enabled = 1
                  GROUP BY settingName
              )
        """, (userID, userID))
        rows = cursor.fetchall()
        cursor.close()
        return {name: value for name, value in rows}
    except Exception:
        return {}

def insertIntoReportTable(userID:str, report_type:str, file_path:str) -> bool:
    db = getDB()
    if db.connection is None:
        print("Database connection is not initialized. Cannot update schema.")
        return False
    print("Updating Report Table in database schema...")
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO report (userID, reportType, filePath, generatedAt)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(userID) DO UPDATE SET
            reportType = excluded.reportType,
            filePath = excluded.filePath,
            generatedAt = datetime('now')
            """, (userID, report_type, file_path)
        )
        db.connection.commit()
        cursor.close()
        print("Report Table updated successfully.")
        return True
    except Exception as e:
        print(f"Error updating Report Table: {e}")
        return False

def insertIntoActivityLogTable(userID: str, appID: int, action: str, category: Optional[str] = None,
                          reason: Optional[str] = None, duration: Optional[int] = None) -> bool:
    db = getDB()
    if db.connection is None:
        print("Database connection is not initialized. Cannot update schema.")
        return False
    print("Updating Activity Log Table in database schema...")
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO activity_log (userID, appID, action, category, reason, duration)
            VALUES (?, ?, ?, ?, ?, ?)
                """, (userID, appID, action, category, reason, duration)
        )
        db.connection.commit()
        cursor.close()
        print("Activity Log Table updated successfully.")
        return True
    except Exception as e:
        print(f"Error updating Activity Log Table: {e}")
        return False

def insertIntoKeystrokeSummaryTable(eventID: int, intervalStart: str, intervalEnd: str, keyCount: int,
                               keysPerMinute: Optional[int] = None, keyCategories: Optional[str] = None,
                               idleSeconds: int = 0) -> bool:
    db = getDB()
    if db.connection is None:
        print("Database connection is not initialized. Cannot update schema.")
        return False
    print("Updating Keystroke Summary Table in database schema...")
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO keystroke_summary (eventID, intervalStart, intervalEnd, keyCount, keysPerMinute, keyCategories, idleSeconds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (eventID, intervalStart, intervalEnd, keyCount, keysPerMinute, keyCategories, idleSeconds)
        )
        db.connection.commit()
        cursor.close()
        print("Keystroke Summary Table updated successfully.")
        return True
    except Exception as e:
        print(f"Error updating Keystroke Summary Table: {e}")
        return False

def insertIntoAlertTable(userID: str, alertType: str, severity: str, message: str,
                         appID: Optional[int] = None, response: Optional[str] = None) -> Optional[int]:
    """Insert alert and return the new alertID."""
    db = getDB()
    if db.connection is None:
        print("Database connection is not initialized.")
        return None
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO alert (userID, appID, severity, alertType, message, response, createdAt)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (userID, appID, severity, alertType, message, response)
        )
        alert_id = cursor.lastrowid
        db.connection.commit()
        cursor.close()
        return alert_id
    except Exception as e:
        logging.getLogger('app').error(f"Error inserting alert into database: {e}")
        print(f"Error inserting alert: {e}")
        return None


#Update tables
def updateAlertResponse(alertID: int, response: str) -> bool:
    """Update alert response to 'dismissed' or 'resolved'."""
    db = getDB()
    if db.connection is None:
        return False
    try:
        cursor = db.connection.cursor()
        cursor.execute("UPDATE alert SET response = ? WHERE alertID = ?", (response, alertID))
        db.connection.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error updating alert response: {e}")
        return False

def getOrCreateAppID(appName: str, executablePath: str) -> Optional[int]:
    """Look up an application by path, or create it. Returns appID."""
    db = getDB()
    if db.connection is None:
        return None
    try:
        cursor = db.connection.cursor()
        cursor.execute("SELECT appID FROM application WHERE executablePath = ? LIMIT 1", (executablePath,))
        row = cursor.fetchone()
        if row:
            cursor.close()
            return row[0]
        cursor.execute(
            "INSERT INTO application (appName, executablePath) VALUES (?, ?)",
            (appName, executablePath)
        )
        app_id = cursor.lastrowid
        db.connection.commit()
        cursor.close()
        return app_id
    except Exception as e:
        print(f"Error in getOrCreateAppID: {e}")
        return None
            
#global instance
spyglassDB: Optional[DatabaseManager] = None
