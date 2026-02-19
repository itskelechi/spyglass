import os
import sqlite3
from pathlib import Path
from typing import Optional

# Import sqlcipher3 as sqlite3 replacement for encrypted databases
try:
    import sqlcipher3 as sqlite3
except ImportError:
    import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

class DatabaseManager:
    # Manage Spyglass database
    def __init__(self, db_path: str = "spyglass.db"):
        self.engine: Optional[Engine] = None
        self.SessionLocal = None
        self.db_path = db_path
        
    def initializeDB(self, create_tables: bool = True, encryption_key: str = "spyglass_default_key") -> None:
        # Initialize the encrypted database and create tables if needed
        print("Initializing Spyglass database with SQLCipher encryption...")
        
        try:
            # Use standard SQLite URL (but sqlcipher3 will handle encryption)
            db_url = f"sqlite:///{self.db_path}"      
            self.engine = create_engine(db_url, connect_args={
                "uri": True,
                "timeout": 30,
                "check_same_thread": False
            }, echo=False)
            
            # Set encryption key for SQLCipher
            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                # Set the encryption key
                cursor.execute(f"PRAGMA key = '{encryption_key}'")
                cursor.close()
            
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            if create_tables:
                self.createAppSchema()
                print("Database initialized and tables created successfully.")
            
        except Exception as e:
            print(f"Error constructing database URL: {e}")
                  
    def createAppSchema(self) -> None:
        # Create necessary tables in the database: USER INFO, KEYSTROKE LOGS, EVENT LOGS, ALERTS, SCREENSHOTS
        print("Creating database tables...")
        
        if self.engine is None:
            print("Database engine is not initialized. Cannot create tables.")
            return
        
        try:
            with self.engine.connect() as connection:
                connection.execute("""
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
                    userID        INTEGER PRIMARY KEY,
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
                    userID                   INTEGER NOT NULL,
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
                    userID       INTEGER NOT NULL,
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
                    userID      INTEGER NOT NULL,
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
                        FOREIGN KEY (eventID) REFERENCES event(eventID)
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
                        FOREIGN KEY (eventID) REFERENCES event(eventID)
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
                        FOREIGN KEY (eventID) REFERENCES event(eventID)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    );

                    -- -------------------------
                    -- ALERT
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS alert (
                    alertID      INTEGER PRIMARY KEY AUTOINCREMENT,
                    userID       INTEGER NOT NULL,
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
                    ON activity_log (user_id, timestamp);

                    CREATE INDEX IF NOT EXISTS idx_activity_app_time
                    ON activity_log (app_id, timestamp);

                    CREATE INDEX IF NOT EXISTS idx_event_activity_time
                    ON event (activity_id, timestamp);

                    CREATE INDEX IF NOT EXISTS idx_alert_user_time
                    ON alert (user_id, timestamp);

                    CREATE INDEX IF NOT EXISTS idx_threshold_app
                    ON privacy_threshold (app_id);

                    CREATE INDEX IF NOT EXISTS idx_report_user_time
                    ON report (user_id, generated_at);

                """)
                print("Tables created successfully.")
        except Exception as e:
            print(f"Error creating tables: {e}")
        
    def closeDB(self) -> None:
        # Close the database connection
        if self.engine:
            self.engine.dispose()
            print("Database connection closed.")
    
    def verifyConnection(self) -> bool:
        # Verify that the database connection is working
        if self.engine is None:
            print("Database engine is not initialized.")
            return False
        
        try:
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            print("Database connection verified successfully.")
            return True
        except Exception as e:
            print(f"Database connection verification failed: {e}")
            return False
    
    def UpdateUserTable(self, deviceInfo: dict) -> bool:
        #Store device information in the user table
        
        if self.engine is None:
            print("Database engine is not initialized.")
            return False
        
        try:
            import json
            
            sysInfo = deviceInfo.get('system', {})
            hardwareInfo = deviceInfo.get('hardware', {})
            
            # Format userSystem as: osType osVersion osBuild
            userSystem = f"{sysInfo.get('os', '')} {sysInfo.get('os_version', '')} (Build {sysInfo.get('os_build', '')})".strip()
            
            # Use hostname as username
            username = sysInfo.get('hostname', '')
            
            # Machine ID
            machineID = hardwareInfo.get('machine_id', '')
            
            # Full system info as JSON
            systemInfo = json.dumps(deviceInfo)
            
            #getprocessor info
            processor = hardwareInfo.get('processor', '')
            
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
            
            with self.engine.connect() as connection:
                connection.execute(insert_query, values)
                connection.commit()
            
            print(f"Device information stored successfully for user {machineID}.")
            return True
        except Exception as e:
            print(f"Error storing device information: {e}")
            return False
    
    def getUserInfo(self, user_id: int) -> Optional[dict]:
        """Retrieve device information from the user table"""
        if self.engine is None:
            print("Database engine is not initialized.")
            return None
        
        try:
            import json
            
            query = "SELECT systemInfo FROM user WHERE userID = ? LIMIT 1"
            
            with self.engine.connect() as connection:
                result = connection.execute(query, (user_id,)).fetchone()
            
            if result and result[0]:
                return json.loads(result[0])
            return None
        except Exception as e:
            print(f"Error retrieving device information: {e}")
            return None

#global instance
spyglassDB: Optional[DatabaseManager] = None

def getDB() -> DatabaseManager:
    global spyglassDB
    if spyglassDB is None:
        spyglassDB = DatabaseManager()
        spyglassDB.initializeDB(create_tables=True)
    return spyglassDB

#Update tables
def updateAppSchema() -> None:
    # Add entries
    print("Updating database schema if necessary...")
    
    db = getDB()
    if db.engine is None:
        print("Database engine is not initialized. Cannot update schema.")
        return
    
    try:
        with db.engine.connect() as connection:
            # Example: Add a new column to the user table for last login time
            connection.execute("""
                INSERT INTO user (userSystem, email, processor, passwordHash)
                VALUES (
            """)
            print("Database schema updated successfully.")
    except Exception as e:
        print(f"Error updating database schema: {e}")

