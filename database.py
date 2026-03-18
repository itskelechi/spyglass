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
            
            # Set encryption key for SQLCipher
            if USING_SQLCIPHER:
                cursor = self.connection.cursor()
                cursor.execute(f"PRAGMA key = '{encryption_key}'")
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
                    PRAGMA cipher_page_size = 4096;
                    PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512;
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
                    -- PRIVACY_THRESHOLD
                    -- (thresholds defined per app in ERD)
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS privacy_threshold (
                    thresholdID               INTEGER PRIMARY KEY AUTOINCREMENT,
                    appID                     INTEGER NOT NULL,
                    maxKeystrokesPerMin       INTEGER,
                    maxScreenAccessPerHour    INTEGER,
                    maxRuntimeMinutes         INTEGER,
                    createdAt                 TEXT    NOT NULL DEFAULT (datetime('now')),

                    CONSTRAINT fk_threshold_app
                        FOREIGN KEY (appID) REFERENCES application(appID)
                        ON DELETE CASCADE ON UPDATE CASCADE
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
                    userID       TEXT NOT NULL,
                    appID        INTEGER NOT NULL,
                    thresholdID  INTEGER NOT NULL,
                    timestamp     TEXT    NOT NULL DEFAULT (datetime('now')),
                    alertType    TEXT    NOT NULL,     -- e.g., excessive_keystrokes, invasive_tos
                    severity      TEXT    NOT NULL,     -- e.g., low/medium/high/critical
                    dismissed     TEXT,                -- datetime when dismissed
                    resolved      INTEGER NOT NULL DEFAULT 0, -- boolean (0/1)

                    CONSTRAINT fk_alert_user
                        FOREIGN KEY (userID) REFERENCES user(userID)
                        ON DELETE CASCADE ON UPDATE CASCADE,

                    CONSTRAINT fk_alert_app
                        FOREIGN KEY (appID) REFERENCES application(appID)
                        ON DELETE CASCADE ON UPDATE CASCADE,

                    CONSTRAINT fk_alert_threshold
                        FOREIGN KEY (thresholdID) REFERENCES privacy_threshold(thresholdID)
                        ON DELETE CASCADE ON UPDATE CASCADE,

                    CONSTRAINT ck_alert_resolved_bool CHECK (resolved IN (0,1))
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

                    CREATE INDEX IF NOT EXISTS idx_alert_user_time
                    ON alert (userID, timestamp);

                    CREATE INDEX IF NOT EXISTS idx_threshold_app
                    ON privacy_threshold (appID);

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
    
    def UpdateUserTable(self, deviceInfo: dict) -> bool:
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

def getDB() -> DatabaseManager:
    global spyglassDB
    if spyglassDB is None:
        spyglassDB = DatabaseManager()
        spyglassDB.initializeDB(create_tables=True, encryption_key="spyglass_default_key")
    return spyglassDB

#Update tables
def updateAppTable(appName: str, executablePath: str, vendor: Optional[str] = None) -> bool:
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

def updateMonitoringSettingsTable(userID: str, aggressivenessLevel: str, screenshotInterval: Optional[int] = None,
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

def updatePrivacyThresholdTable(appID: int, maxKeystrokesPerMin: Optional[int] = None,
                               maxScreenAccessPerHour: Optional[int] = None, maxRuntimeMinutes: Optional[int] = None) -> bool:
    db = getDB()
    if db.connection is None:
        print("Database connection is not initialized. Cannot update schema.")
        return False
    print("Updating Privacy Threshold Table in database schema...")
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO privacy_threshold (thresholdID, appID, maxKeystrokesPerMin, maxScreenAccessPerHour, maxRuntimeMinutes, createdAt)
            VALUES (NULL, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(appID) DO UPDATE SET
            maxKeystrokesPerMin = excluded.maxKeystrokesPerMin, 
            maxScreenAccessPerHour = excluded.maxScreenAccessPerHour,
            maxRuntimeMinutes = excluded.maxRuntimeMinutes,
            createdAt = datetime('now')
            """, (appID, maxKeystrokesPerMin, maxScreenAccessPerHour, maxRuntimeMinutes)
        )
        db.connection.commit()
        cursor.close()
        print("Privacy Threshold Table updated successfully.")
        return True
    except Exception as e:
        print(f"Error updating Privacy Threshold Table: {e}")
        return False

def updateReportTable(userID:str, report_type:str, file_path:str) -> bool:
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

def updateActivityLogTable(userID: str, appID: int, action: str, category: Optional[str] = None,
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

def updateKeystrokeSummaryTable(eventID: int, intervalStart: str, intervalEnd: str, keyCount: int,
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

def updateAlertTable(userID: str, appID: int, thresholdID: int, alertType: str, severity: str,
                     dismissed: Optional[str] = None, resolved: bool = False) -> bool:
    db = getDB()
    if db.connection is None:
        print("Database connection is not initialized. Cannot update schema.")
        return False
    print("Updating Alert Table in database schema...")
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO alert (userID, appID, thresholdID, alertType, severity, dismissed, resolved)
            VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(alertID) DO UPDATE SET
                userID = excluded.userID,
                appID = excluded.appID,
                thresholdID = excluded.thresholdID,
                alertType = excluded.alertType,
                severity = excluded.severity,
                dismissed = excluded.dismissed,
                resolved = excluded.resolved
                """, (userID, appID, thresholdID, alertType, severity, dismissed, resolved)
        )
        db.connection.commit()
        cursor.close()
        print("Alert Table updated successfully.")
        return True
    except Exception as e:
        print(f"Error updating Alert Table: {e}")
        return False
            
#global instance
spyglassDB: Optional[DatabaseManager] = None
