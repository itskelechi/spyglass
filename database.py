import os
import sqlite3
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, 
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

class DatabaseManager:
    # Manage Spyglass database
    def __init__(self, db_path: str = "spyglass.db"):
        self.engine: Optional[Engine] = None
        self.SessionLocal = None
        self.db_path = db_path
        
    def initializeDB(self, create_tables: bool = True) -> None:
        # Initialize the database and create tables if needed
        print("Initializing Spyglass database...")
        
        try:
            db_url = f"sqlite:///{self.db_path}"      
            self.engine = create_engine(db_url, connect_args={
                "uri": True,
                "timeout": 30,
                "check_same_thread": False
            }, echo=False)
            
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            if create_tables:
                self.createTables()
                print("Database initialized and tables created successfully.")
            
        except Exception as e:
            print(f"Error constructing database URL: {e}")
                  
    def createTables(self) -> None:
        # Create necessary tables in the database: USER INFO, KEYSTROKE LOGS, EVENT LOGS, ALERTS, SCREENSHOTS
        print("Creating database tables...")
        
        if self.engine is None:
            print("Database engine is not initialized. Cannot create tables.")
            return
        
        try:
            with self.engine.connect() as connection:
                connection.execute("""
                    PRAGMA foreign_keys = ON;

                    -- -------------------------
                    -- USER
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS user (
                    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    system       TEXT    NOT NULL,
                    processor          TEXT    NOT NULL,
                    password_hash  TEXT    NOT NULL,
                    created_at     TEXT    NOT NULL DEFAULT (datetime('now')),

                    CONSTRAINT uq_user_system UNIQUE (system),
                    CONSTRAINT uq_user_processor    UNIQUE (processor)
                    );

                    -- -------------------------
                    -- APPLICATION
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS application (
                    app_id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_name         TEXT    NOT NULL,
                    executable_path  TEXT    NOT NULL,
                    vendor           TEXT,

                    CONSTRAINT uq_application_exec_path UNIQUE (executable_path)
                    );

                    -- -------------------------
                    -- MONITORING_SETTINGS
                    -- (one row per user)
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS monitoring_settings (
                    settings_id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id                   INTEGER NOT NULL,
                    aggressiveness_level      TEXT    NOT NULL,           -- e.g., low/medium/high
                    screenshot_interval       INTEGER,                    -- seconds/minutes (define in app)
                    keystroke_logging_enabled INTEGER NOT NULL DEFAULT 0, -- boolean (0/1)
                    app_monitoring_enabled    INTEGER NOT NULL DEFAULT 1, -- boolean (0/1)
                    max_storage_mb            INTEGER NOT NULL DEFAULT 500,

                    CONSTRAINT fk_settings_user
                        FOREIGN KEY (user_id) REFERENCES user(user_id)
                        ON DELETE CASCADE ON UPDATE CASCADE,

                    CONSTRAINT uq_settings_user UNIQUE (user_id),

                    CONSTRAINT ck_settings_keystroke_bool CHECK (keystroke_logging_enabled IN (0,1)),
                    CONSTRAINT ck_settings_appmon_bool    CHECK (app_monitoring_enabled IN (0,1))
                    );

                    -- -------------------------
                    -- PRIVACY_THRESHOLD
                    -- (thresholds defined per app in ERD)
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS privacy_threshold (
                    threshold_id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_id                     INTEGER NOT NULL,
                    max_keystrokes_per_min     INTEGER,
                    max_screen_access_per_hour INTEGER,
                    max_runtime_minutes        INTEGER,
                    created_at                 TEXT    NOT NULL DEFAULT (datetime('now')),

                    CONSTRAINT fk_threshold_app
                        FOREIGN KEY (app_id) REFERENCES application(app_id)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    );

                    -- -------------------------
                    -- REPORT
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS report (
                    report_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id       INTEGER NOT NULL,
                    report_type   TEXT    NOT NULL,     -- e.g., daily_summary, incident_report
                    file_path     TEXT    NOT NULL,
                    generated_at  TEXT    NOT NULL DEFAULT (datetime('now')),

                    CONSTRAINT fk_report_user
                        FOREIGN KEY (user_id) REFERENCES user(user_id)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    );

                    -- -------------------------
                    -- ACTIVITY_LOG
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS activity_log (
                    activity_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id      INTEGER NOT NULL,
                    app_id       INTEGER NOT NULL,
                    timestamp    TEXT    NOT NULL DEFAULT (datetime('now')),
                    action       TEXT    NOT NULL,      -- e.g., launched, focused, closed
                    category     TEXT,                  -- e.g., productivity, browser, unknown
                    reason       TEXT,                  -- optional justification/explanation
                    duration     INTEGER,               -- seconds

                    CONSTRAINT fk_activity_user
                        FOREIGN KEY (user_id) REFERENCES user(user_id)
                        ON DELETE CASCADE ON UPDATE CASCADE,

                    CONSTRAINT fk_activity_app
                        FOREIGN KEY (app_id) REFERENCES application(app_id)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    );

                    -- -------------------------
                    -- EVENT
                    -- (granular events under an activity log)
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS event (
                    event_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity_id   INTEGER NOT NULL,
                    timestamp     TEXT    NOT NULL DEFAULT (datetime('now')),
                    process_id    INTEGER,
                    process_name  TEXT,
                    event_type    TEXT    NOT NULL,   -- e.g., process_start, file_access, window_focus
                    duration      INTEGER,            -- seconds

                    CONSTRAINT fk_event_activity
                        FOREIGN KEY (activity_id) REFERENCES activity_log(activity_id)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    );

                    -- -------------------------
                    -- KEYSTROKE_SUMMARY
                    -- (metadata summary per event, NOT raw keys)
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS keystroke_summary (
                    keystroke_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id         INTEGER NOT NULL,
                    interval_start   TEXT    NOT NULL,
                    interval_end     TEXT    NOT NULL,
                    key_count        INTEGER NOT NULL DEFAULT 0,
                    keys_per_minute  INTEGER,
                    key_categories   TEXT,            -- e.g., "letters, numbers, backspace"
                    idle_seconds     INTEGER NOT NULL DEFAULT 0,

                    CONSTRAINT fk_keystroke_event
                        FOREIGN KEY (event_id) REFERENCES event(event_id)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    );

                    -- -------------------------
                    -- SCREENSHOT
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS screenshot (
                    screenshot_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id       INTEGER NOT NULL,
                    image_path     TEXT    NOT NULL,
                    captured_at    TEXT    NOT NULL DEFAULT (datetime('now')),

                    CONSTRAINT fk_screenshot_event
                        FOREIGN KEY (event_id) REFERENCES event(event_id)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    );

                    -- -------------------------
                    -- VIDEO_RECORDING
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS video_recording (
                    video_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id          INTEGER NOT NULL,
                    video_path        TEXT    NOT NULL,
                    duration_seconds  INTEGER NOT NULL DEFAULT 0,

                    CONSTRAINT fk_video_event
                        FOREIGN KEY (event_id) REFERENCES event(event_id)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    );

                    -- -------------------------
                    -- ALERT
                    -- -------------------------
                    CREATE TABLE IF NOT EXISTS alert (
                    alert_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id       INTEGER NOT NULL,
                    app_id        INTEGER NOT NULL,
                    threshold_id  INTEGER NOT NULL,
                    timestamp     TEXT    NOT NULL DEFAULT (datetime('now')),
                    alert_type    TEXT    NOT NULL,     -- e.g., excessive_keystrokes, invasive_tos
                    severity      TEXT    NOT NULL,     -- e.g., low/medium/high/critical
                    dismissed     TEXT,                -- datetime when dismissed
                    resolved      INTEGER NOT NULL DEFAULT 0, -- boolean (0/1)

                    CONSTRAINT fk_alert_user
                        FOREIGN KEY (user_id) REFERENCES user(user_id)
                        ON DELETE CASCADE ON UPDATE CASCADE,

                    CONSTRAINT fk_alert_app
                        FOREIGN KEY (app_id) REFERENCES application(app_id)
                        ON DELETE CASCADE ON UPDATE CASCADE,

                    CONSTRAINT fk_alert_threshold
                        FOREIGN KEY (threshold_id) REFERENCES privacy_threshold(threshold_id)
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