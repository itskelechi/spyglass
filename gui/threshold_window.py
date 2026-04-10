"""Threshold Configuration Window — Glass UI design."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QFrame, QScrollArea, QWidget, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QFont, QPainter, QColor, QLinearGradient, QRadialGradient

from gui.styles import COLORS, SEVERITY_COLORS
from gui.glass_widgets import GradientBackground, GlassPanel


# Threshold definitions: (key, label, unit, min, max, defaults)
BASIC_THRESHOLDS = [
    ("cpu_limit", "CPU Usage", "%", 1, 100, {"low": 30, "medium": 55, "high": 70, "critical": 90}),
    ("memory_limit", "Memory Usage", "%", 1, 100, {"low": 40, "medium": 65, "high": 75, "critical": 90}),
    ("process_activity", "Process Activity (scripts)", "scripts", 1, 500, {"low": 20, "medium": 50, "high": 100, "critical": 200}),
    ("same_script_limit", "Same-App Script Limit", "scripts", 1, 200, {"low": 10, "medium": 20, "high": 50, "critical": 100}),
]

ADVANCED_THRESHOLDS = [
    ("keystroke_frequency", "Keystroke Frequency", "keys/min", 1, 2000, {"low": 40, "medium": 60, "high": 100, "critical": 120}),
    ("modifier_key_threshold", "Modifier Key Combinations", "combos", 1, 500, {"low": 10, "medium": 25, "high": 50, "critical": 75}),
]

SEVERITIES = ["low", "medium", "high", "critical"]


class ThresholdWindow(QDialog, GradientBackground):
    #monitoring config dialog
    thresholds_configured = pyqtSignal(dict)

    def __init__(self, monitoring_level: str = "LOW", parent=None):
        super().__init__(parent)
        self.monitoring_level = monitoring_level.upper()
        self.setWindowTitle("Spyglass — Configure Thresholds")
        self.setMinimumSize(780, 620)
        self.setModal(True)
        self.spinboxes: dict[str, dict[str, QSpinBox]] = {}
        self.build_ui()

    def paintEvent(self, event):
        self.paint_gradient_bg(event)

    def build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 24)
        outer.setSpacing(16)

        # Header
        header = QLabel("T H R E S H O L D   S E T T I N G S")
        header.setFont(QFont("JetBrains Mono", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(f"color: {COLORS['accent_steel']}; background: transparent;")
        outer.addWidget(header)

        desc = QLabel(
            "Set thresholds for alerts at each severity level. "
            "Press Reset to restore defaults."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 13px; background: transparent;"
        )
        outer.addWidget(desc)

        # Glass container for scrollable content
        glass = GlassPanel()
        glass_lay = QVBoxLayout(glass)
        glass_lay.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setSpacing(14)
        self._content_layout.setContentsMargins(16, 16, 16, 16)
        scroll.setWidget(content)
        glass_lay.addWidget(scroll)
        outer.addWidget(glass, 1)

        # --- sections
        self._add_section("BASIC THRESHOLDS", BASIC_THRESHOLDS)

        if self.monitoring_level == "HIGH":
            self._add_section("ADVANCED THRESHOLDS  (HIGH mode)", ADVANCED_THRESHOLDS)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_reset = QPushButton("Reset Defaults")
        btn_reset.setObjectName("secondary")
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.setStyleSheet(
            f"""
            QPushButton {{
                background: {COLORS['panel_fill_soft']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['panel_border']};
                border-radius: 8px;
                padding: 10px 28px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['panel_hover']};
                color: {COLORS['text_primary']};
            }}
            """
        )
        btn_reset.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(btn_reset)

        btn_save = QPushButton("Save Thresholds")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(234,242,255,0.22),
                    stop:1 rgba(124,141,255,0.22)
                );
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['panel_border_strong']};
                border-radius: 10px;
                padding: 10px 32px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(234,242,255,0.28),
                    stop:1 rgba(124,141,255,0.30)
                );
            }}
            """
        )
        btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(btn_save)

        outer.addLayout(btn_layout)

    # ── section helpers ──────────────────────────────────────────

    def _add_section(self, title: str, thresholds: list):
        section_label = QLabel(title)
        section_label.setFont(QFont("JetBrains Mono", 11, QFont.Weight.Bold))
        section_label.setStyleSheet(
            f"color: {COLORS['accent_steel']}; background: transparent; margin-top: 4px;"
        )
        self._content_layout.addWidget(section_label)

        for key, label, unit, min_val, max_val, defaults in thresholds:
            self._add_threshold_row(key, label, unit, min_val, max_val, defaults)

    def _add_threshold_row(self, key, label, unit, min_val, max_val, defaults):
        card = GlassPanel()
        grid = QGridLayout(card)
        grid.setContentsMargins(18, 14, 18, 14)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(6)

        # Row title
        title = QLabel(f"{label}  ({unit})")
        title.setFont(QFont("Inter UI", 11, QFont.Weight.Bold))
        title.setStyleSheet(
            f"color: {COLORS['text_primary']}; background: transparent;"
        )
        grid.addWidget(title, 0, 0, 1, 4)

        self.spinboxes[key] = {}

        spin_style = f"""
            QSpinBox {{
                background: rgba(255,255,255,0.05);
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['panel_border']};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background: {COLORS['panel_fill']};
                border: none;
                width: 16px;
            }}
        """

        for col, severity in enumerate(SEVERITIES):
            sev_label = QLabel(severity.upper())
            sev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sev_label.setFont(QFont("Inter UI", 10, QFont.Weight.Bold))
            sev_label.setStyleSheet(
                f"color: {SEVERITY_COLORS[severity.upper()]}; background: transparent;"
            )
            grid.addWidget(sev_label, 1, col)

            spin = QSpinBox()
            spin.setRange(min_val, max_val)
            spin.setValue(defaults[severity])
            spin.setSuffix(f" {unit}" if len(unit) <= 3 else "")
            spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin.setMinimumWidth(110)
            spin.setProperty("default", defaults[severity])
            spin.setStyleSheet(spin_style)
            grid.addWidget(spin, 2, col)
            self.spinboxes[key][severity] = spin

        self._content_layout.addWidget(card)

    # ── actions ──────────────────────────────────────────────────

    def _reset_defaults(self):
        for key_dict in self.spinboxes.values():
            for spin in key_dict.values():
                spin.setValue(spin.property("default"))

    def _on_save(self):
        result = {}
        for key, sev_dict in self.spinboxes.items():
            result[key] = {sev: spin.value() for sev, spin in sev_dict.items()}
        self.thresholds_configured.emit(result)
        self.accept()

    def get_thresholds(self) -> dict:
        result = {}
        for key, sev_dict in self.spinboxes.items():
            result[key] = {sev: spin.value() for sev, spin in sev_dict.items()}
        return result
