"""Consent Window — Glass UI design with gradient background."""

import os

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QTextEdit, QWidget, QFrame,
    QScrollArea, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QFont, QPainter, QColor, QLinearGradient, QRadialGradient, QPen, QPixmap, QIcon

LOGO = os.path.join(os.path.dirname(__file__), "logo", "spyglass_logo.png")

from gui.styles import COLORS
from gui.glass_widgets import GradientBackground, GlassPanel


class ConsentWindow(QDialog, GradientBackground):
    """Consent dialog with full Glass UI styling."""

    consent_given = pyqtSignal(str)
    consent_declined = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spyglass — User Consent")
        self.setModal(True)
        if os.path.isfile(LOGO):
            self.setWindowIcon(QIcon(LOGO))
        # Cap at 620×700 so content fits without buttons getting lost
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            w = min(620, int(avail.width() * 0.55))
            h = min(700, int(avail.height() * 0.8))
            self.resize(w, h)
        else:
            self.resize(620, 700)
        self.setMaximumWidth(620)
        self.build_ui()

    def paintEvent(self, event):
        self.paint_gradient_bg(event)
        super().paintEvent(event)

    def build_ui(self):
        outer = QVBoxLayout(self)
        outer.setSpacing(0)
        outer.setContentsMargins(0, 0, 0, 0)

        # Scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(body)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 12, 40, 12)

        # Logo + SPYGLASS header
        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        title_row.addStretch()
        if os.path.isfile(LOGO):
            logo_label = QLabel()
            pixmap = QPixmap(LOGO).scaled(
                80, 120, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo_label.setPixmap(pixmap)
            logo_label.setStyleSheet("background: transparent;")
            title_row.addWidget(logo_label)
        header = QLabel("WELCOME TO SPYGLASS")
        header.setFont(QFont("Bungee Hairline", 24, QFont.Weight.DemiBold))
        header.setStyleSheet(f"color: {COLORS['text_primary']}; letter-spacing: 4px;")
        title_row.addWidget(header)
        title_row.addStretch()
        layout.addLayout(title_row)
        layout.addSpacing(-32)

        sub = QLabel("USER CONSENT AGREEMENT")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 18px; font-family: 'Gruppo', 'Segoe UI', Arial, sans-serif; letter-spacing: 2px;")
        layout.addWidget(sub)
        layout.addSpacing(-5)

        # Disclosure in glass panel
        disclosure_panel = GlassPanel(radius=10, bg_alpha=70)
        dp_layout = QVBoxLayout(disclosure_panel)
        dp_layout.setContentsMargins(12, 8, 12, 8)

        disclosure = QTextEdit()
        disclosure.setReadOnly(True)
        disclosure.setHtml(self._disclosure_html())
        disclosure.setMinimumHeight(250)
        disclosure.setStyleSheet(
            f"background: transparent; border: none; color: {COLORS['text_secondary']};"
        )
        dp_layout.addWidget(disclosure)
        layout.addWidget(disclosure_panel)

        # Monitoring level in glass panel
        level_panel = GlassPanel(radius=10, bg_alpha=60)
        level_layout = QVBoxLayout(level_panel)
        level_layout.setContentsMargins(20, 16, 20, 16)

        level_label = QLabel("SELECT YOUR MONITORING PREFERENCE")
        level_label.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        level_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        level_label.setStyleSheet(f"letter-spacing: 2px; color: {COLORS['text_primary']};")
        level_layout.addWidget(level_label)
        level_layout.addSpacing(5)

        self.level_group = QButtonGroup(self)

        self.radio_low = QRadioButton(
            "LOW  —  Basic monitoring (processes, system info)"
        )
        self.radio_low.setStyleSheet(f"font-size: 12px; padding: 2px; color: {COLORS['text_primary']}; font-family: 'Gruppo', 'Segoe UI', Arial, sans-serif; letter-spacing: 1px;")
        self.level_group.addButton(self.radio_low)
        level_layout.addWidget(self.radio_low)

        self.radio_high = QRadioButton(
            "HIGH  —  Full monitoring (includes keystroke logging)"
        )
        self.radio_high.setStyleSheet(f"font-size: 12px; padding: 2px; color: {COLORS['text_primary']}; font-family: 'Gruppo', 'Segoe UI', Arial, sans-serif; letter-spacing: 1px;")
        self.level_group.addButton(self.radio_high)
        level_layout.addWidget(self.radio_high)

        self.radio_low.setChecked(True)
        layout.addWidget(level_panel)

        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        # Buttons — pinned below scroll area, always visible
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(40, 12, 40, 20)
        btn_layout.addStretch()

        self.btn_decline = QPushButton("Decline")
        self.btn_decline.setObjectName("danger")
        self.btn_decline.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_decline.clicked.connect(self._on_decline)
        btn_layout.addWidget(self.btn_decline)
        btn_layout.addSpacing(12)

        self.btn_accept = QPushButton("Accept")
        self.btn_accept.setObjectName("accent")
        self.btn_accept.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_accept.clicked.connect(self._on_accept)
        btn_layout.addWidget(self.btn_accept)

        outer.addLayout(btn_layout)

    def _on_accept(self):
        level = "HIGH" if self.radio_high.isChecked() else "LOW"
        self.consent_given.emit(level)
        self.accept()

    def _on_decline(self):
        self.consent_declined.emit()
        self.reject()

    def get_selected_level(self) -> str:
        return "HIGH" if self.radio_high.isChecked() else "LOW"

    @staticmethod
    def _disclosure_html() -> str:
        return f"""
        <div style="font-family: Gruppo; font-size: 13px; line-height: 1.9; color: {COLORS['text_secondary']}; letter-spacing: 1px; font-weight: 700;">
        <h3 style="color: {COLORS['text_primary']}; letter-spacing: 2px;">MONITORING DISCLOSURE</h3>
        <p style="color: {COLORS['accent_red']}; font-weight: bold;">
        &#9888; This application captures sensitive data.
        </p>
        <p>This application will monitor and log the following activities on your device:</p>

        <h4 style="color: {COLORS['text_primary']};">BASIC MONITORING (All Levels)</h4>
        <ul>
            <li>Process / Application execution and activity</li>
            <li>System performance metrics</li>
            <li>Device information (OS, hardware, network)</li>
            <li>General activity timestamps</li>
        </ul>

        <h4 style="color: {COLORS['text_primary']};">ADVANCED MONITORING (High Level Only)</h4>
        <ul>
            <li>Keystroke activity (keyboard input tracking)</li>
            <li>Character frequency analysis</li>
            <li>Modifier key combinations</li>
        </ul>

        <hr style="border-color: rgba(100,120,200,0.2);">

        <h4 style="color: {COLORS['text_primary']};">PRIVACY &amp; DATA USAGE</h4>
        <ul>
            <li>All data is stored locally on your device</li>
            <li>Data is encrypted using SQLCipher</li>
            <li>No data is transmitted without explicit consent</li>
            <li>You can disable monitoring at any time</li>
        </ul>

        <h4 style="color: {COLORS['text_primary']};">ADMIN PRIVILEGES</h4>
        <ul>
            <li>This application requires Windows Administrator privileges</li>
            <li>Admin access is needed to monitor system-level activities</li>
        </ul>

        <hr style="border-color: rgba(100,120,200,0.2);">
        <p>By clicking <b style="color: white;">I Accept</b>, you acknowledge that you understand and consent to
        the monitoring activities described above.</p>
        </div>
        """
