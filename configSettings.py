import json
import os
from typing import Dict, Any


class ConfigSettings:
    def __init__(self, config_file: str = "spyglass_settings.json"):
        self.config_file = config_file
        self.config = {}
        self.load_config()

    def load_config(self) -> None:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                print(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                self._set_defaults()
        else:
            self._set_defaults()

    def _set_defaults(self) -> None:
        self.config = {
            "monitoring_level": "LOW",
            "keystroke_logging_enabled": False,
            "app_monitoring_enabled": True,
            "screenshot_interval": 0,
            "video_recording_enabled": False,
            "max_storage_mb": 1000,
            "debug_logging": False,
            "auto_backup_enabled": False,
            "database_encryption": True,
        }

    def set_monitoring_level(self, level: str) -> bool:
        allowed_levels = ["LOW", "MEDIUM", "HIGH"]
        if level.upper() not in allowed_levels:
            print("Invalid monitoring level. Must be 'LOW', 'MEDIUM', or 'HIGH'")
            return False

        level = level.upper()
        self.config["monitoring_level"] = level
        self.config["keystroke_logging_enabled"] = (level == "HIGH")
        self.config["app_monitoring_enabled"] = True

        print(f"Monitoring level set to {level}")
        print(f"  - Keystroke logging: {'ENABLED' if level == 'HIGH' else 'DISABLED'}")
        return True

    def save_config(self) -> bool:
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            print(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_config(self) -> Dict[str, Any]:
        return self.config

    def set_config(self, new_config: Dict[str, Any]) -> None:
        print("Updating configuration with %s" % new_config)
        self.config.update(new_config)

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        self.config[key] = value

    def is_keylogger_enabled(self) -> bool:
        return self.config.get("keystroke_logging_enabled", False)

    def is_app_monitoring_enabled(self) -> bool:
        return self.config.get("app_monitoring_enabled", True)

    def get_monitoring_level(self) -> str:
        return self.config.get("monitoring_level", "LOW")

    def print_settings(self) -> None:
        print("\n" + "=" * 60)
        print("CURRENT MONITORING SETTINGS".center(60))
        print("=" * 60)
        print(f"\nMonitoring Level: {self.config.get('monitoring_level', 'NOT SET')}")
        print("\nEnabled Features:")
        print(f"  • Keystroke Logging:      {'ENABLED' if self.config.get('keystroke_logging_enabled') else 'DISABLED'}")
        print(f"  • App Monitoring:         {'ENABLED' if self.config.get('app_monitoring_enabled') else 'DISABLED'}")
        print(f"  • Screenshot Capture:     {'ENABLED' if self.config.get('screenshot_interval', 0) > 0 else 'DISABLED'}")
        print(f"  • Video Recording:        {'ENABLED' if self.config.get('video_recording_enabled') else 'DISABLED'}")
        print(f"  • Auto Backup:            {'ENABLED' if self.config.get('auto_backup_enabled') else 'DISABLED'}")
        print(f"  • Debug Logging:          {'ENABLED' if self.config.get('debug_logging') else 'DISABLED'}")
        print("\nStorage & Security:")
        print(f"  • Max Storage:            {self.config.get('max_storage_mb', 1000)} MB")
        print(f"  • Database Encryption:    {'ENABLED' if self.config.get('database_encryption') else 'DISABLED'}")
        print("\n" + "=" * 60 + "\n")


def create_config(monitoring_level: str) -> ConfigSettings:
    config = ConfigSettings()
    config.set_monitoring_level(monitoring_level)
    config.save_config()
    return config
