from copy import deepcopy
from typing import Any, Dict


BASE_THRESHOLD_PROFILE: Dict[str, Dict[str, Any]] = {
    "application": {
        "poll_interval_seconds": 5,
        "app_cpu_percent": 95,
        "app_cpu_duration_seconds": 45,
        "background_cpu_percent": 70,
        "background_cpu_duration_seconds": 45,
        "process_count": 220,
        "system_cpu_percent": 95,
        "system_cpu_duration_seconds": 120,
        "spyglass_cpu_percent": 50,
        "unknown_app_min_cpu_percent": 20,
    },
    "keystroke": {
        "fast_typing_kpm": 360,
        "continuous_typing_seconds": 720,
        "pause_reset_seconds": 5,
        "idle_mouse_seconds": 150,
        "mouse_poll_interval_seconds": 1,
    },
    "alerting": {
        "cooldown_seconds": 90,
        "startup_grace_seconds": 30,
    },
}

PROFILE_OVERRIDES: Dict[str, Dict[str, Dict[str, Any]]] = {
    "LOW": {
        "application": {
            "poll_interval_seconds": 6,
            "app_cpu_percent": 97,
            "app_cpu_duration_seconds": 60,
            "background_cpu_percent": 80,
            "background_cpu_duration_seconds": 60,
            "process_count": 260,
            "system_cpu_percent": 97,
            "system_cpu_duration_seconds": 150,
            "spyglass_cpu_percent": 60,
            "unknown_app_min_cpu_percent": 25,
        },
        "keystroke": {
            "fast_typing_kpm": 450,
            "continuous_typing_seconds": 900,
            "pause_reset_seconds": 6,
            "idle_mouse_seconds": 180,
        },
        "alerting": {
            "cooldown_seconds": 120,
            "startup_grace_seconds": 35,
        },
    },
    "MEDIUM": {},
    "HIGH": {
        "application": {
            "poll_interval_seconds": 4,
            "app_cpu_percent": 90,
            "app_cpu_duration_seconds": 35,
            "background_cpu_percent": 65,
            "background_cpu_duration_seconds": 35,
            "process_count": 180,
            "system_cpu_percent": 93,
            "system_cpu_duration_seconds": 90,
            "spyglass_cpu_percent": 50,
            "unknown_app_min_cpu_percent": 15,
        },
        "keystroke": {
            "fast_typing_kpm": 320,
            "continuous_typing_seconds": 600,
            "pause_reset_seconds": 4,
            "idle_mouse_seconds": 120,
        },
        "alerting": {
            "cooldown_seconds": 60,
            "startup_grace_seconds": 25,
        },
    },
}


def deep_update(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_update(base[key], value)
        else:
            base[key] = value
    return base


class ThresholdEngine:
    def __init__(self, monitoring_level: str = "MEDIUM", overrides: Dict[str, Any] | None = None):
        self.monitoring_level = (monitoring_level or "MEDIUM").upper()
        self.overrides = overrides or {}

    def get_thresholds(self) -> Dict[str, Dict[str, Any]]:
        profile = deepcopy(BASE_THRESHOLD_PROFILE)
        deep_update(profile, PROFILE_OVERRIDES.get(self.monitoring_level, {}))
        deep_update(profile, self.overrides)
        return profile
