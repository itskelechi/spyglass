"""Main Dashboard — Glass UI design matching Spyglass wireframes.

Layout:  GlassSidebar (logo-pill + 7 CLI menu items)  |  Stacked pages
Pages:   Home (welcome + power), Settings, Installed Apps, Running Apps,
         Reports, Thresholds
"""

import os
import logging
import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QTextEdit, QProgressBar, QGridLayout,
    QMessageBox, QSizePolicy, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QSpacerItem, QLineEdit, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPainter, QColor, QLinearGradient, QRadialGradient, QPen, QPixmap, QIcon, QPainterPath

# Logo path (resolved relative to this file)
LOGO = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logo", "spyglass_logo.png")

from gui.styles import COLORS, SEVERITY_COLORS, BG_GRADIENT_CSS
from gui.glass_widgets import (
    GradientBackground, GlassPanel, GlassSidebar, PowerButton,
    StatusPill, GlassStatCard,
)
from gui.app_table import InstalledAppsPanel, RunningAppsPanel
from gui.threshold_window import ThresholdWindow
from gui.workers import AlertSignalBridge


# ─────────────────────────────────────────────────────────────────
#  Floating desktop notification (glass pill)
# ─────────────────────────────────────────────────────────────────

class FloatingNotification(QWidget):
    """Top-right desktop toast styled as a glass pill."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(380, 64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 22, 0)
        layout.setSpacing(12)

        self._icon_label = QLabel()
        self._icon_label.setFixedSize(36, 36)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("background: transparent;")
        if os.path.isfile(LOGO):
            pixmap = QPixmap(LOGO).scaled(
                30, 70, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._icon_label.setPixmap(pixmap)
        layout.addWidget(self._icon_label)

        self._text_label = QLabel()
        self._text_label.setFont(QFont("Inter UI", 11))
        self._text_label.setWordWrap(True)
        self._text_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(self._text_label)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        radius = rect.height() / 2

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        fill = QColor(15, 18, 55, 220)
        p.fillPath(path, fill)

        hl = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.bottom()))
        hl.setColorAt(0, QColor(255, 255, 255, 12))
        hl.setColorAt(1, QColor(255, 255, 255, 0))
        p.fillPath(path, hl)

        border = QColor(100, 120, 200, 80)
        p.setPen(QPen(border, 1.2))
        p.drawRoundedRect(rect, radius, radius)
        p.end()

    def show_notification(self, text: str, duration_ms: int = 4000):
        self._text_label.setText(text)
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = geom.right() - self.width() - 20
            y = geom.top() + 20
            self.move(x, y)
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()
        self._hide_timer.start(duration_ms)

    def _fade_out(self):
        self.hide()


# ─────────────────────────────────────────────────────────────────
#  Sidebar nav button
# ─────────────────────────────────────────────────────────────────

class SidebarNavButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(44)
        self.setFont(QFont("Inter", 12, QFont.Weight.DemiBold))
        self._update_style(False)

    def _update_style(self, checked: bool):
        if checked:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(15, 18, 50, 0.55);
                    color: {COLORS['text_primary']};
                    text-align: left;
                    padding-left: 22px;
                    border: none;
                    border-bottom: 2px solid {COLORS['accent_steel']};
                    font-size: 13px;
                    font-weight: 700;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['text_secondary']};
                    text-align: left;
                    padding-left: 22px;
                    border: none;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background: rgba(255,255,255,0.03);
                    color: {COLORS['text_primary']};
                }}
            """)

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._update_style(checked)
        
        
# ─────────────────────────────────────────────────────────────────
#  Small power icon (top-right on Analytics/Reports pages)
# ─────────────────────────────────────────────────────────────────

class MiniPowerIcon(QWidget):
    clicked = pyqtSignal = None  # read-only indicator

    def __init__(self, size: int = 60, parent=None):
        super().__init__(parent)
        self._size = size
        self._active = False
        self.setFixedSize(size, size)

    def set_active(self, active: bool):
        self._active = active
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self._size
        cx, cy = s / 2, s / 2
        r = s * 0.4

        col = QColor(COLORS["accent_green"]) if self._active else QColor(COLORS["accent_red"])

        # Outer glass circle
        p.setPen(QPen(QColor(100, 120, 200, 50), 1))
        p.setBrush(QColor(15, 18, 55, 100))
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Ring
        p.setPen(QPen(col, 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r * 0.68, r * 0.68)

        # Arc + line (power icon)
        icon_pen = QPen(col, 2.5)
        icon_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(icon_pen)
        arc_r = r * 0.38
        arc_rect = QRectF(cx - arc_r, cy - arc_r, arc_r * 2, arc_r * 2)
        p.drawArc(arc_rect, 120 * 16, 300 * 16)
        p.drawLine(QPointF(cx, cy - arc_r - 2), QPointF(cx, cy))
        p.end()


from PyQt6.QtCore import pyqtSignal


# ═════════════════════════════════════════════════════════════════
#  DASHBOARD  MAIN  WINDOW
# ═════════════════════════════════════════════════════════════════

class DashboardWindow(QMainWindow, GradientBackground):

    def __init__(self, spyglass, parent=None):
        super().__init__(parent)
        self.spyglass = spyglass
        self.setWindowTitle("Spyglass")
        self.setMinimumSize(1100, 680)
        self.resize(1280, 760)

        self._alert_bridge = AlertSignalBridge()
        self._alert_bridge.alert_raised.connect(self._on_alert_raised)
        self._alert_count = 0

        # Window icon
        if os.path.isfile(LOGO):
            self.setWindowIcon(QIcon(LOGO))

        self.build_ui()
        self._start_polling()

    # ── gradient background ──────────────────────────────────────
    def paintEvent(self, event):
        self.paint_gradient_bg(event)

    # ── UI Construction ──────────────────────────────────────────
    def build_ui(self):
        central = QWidget()
        central.setStyleSheet("background: transparent;")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # — Sidebar —
        sidebar = self.build_sidebar()
        root.addWidget(sidebar)

        # — Stacked pages (match CLI menu order) —
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        self.stack.addWidget(self._build_home_page())           # 0 – Home / Start Monitoring
        self.stack.addWidget(self._build_settings_page())       # 1 – Show Current Settings
        self.stack.addWidget(self._build_installed_apps_page()) # 2 – View Installed Apps
        self.stack.addWidget(self._build_analytics_page())      # 3 – View Running Apps
        self.stack.addWidget(self._build_reports_page())        # 4 – Show Reports
        root.addWidget(self.stack, 1)

        self._nav_buttons[0].setChecked(True)

        # Floating desktop notification
        self._notification = FloatingNotification()

    # ── Sidebar ──────────────────────────────────────────────────
    def build_sidebar(self) -> GlassSidebar:
        sidebar = GlassSidebar()
        sidebar.setFixedWidth(224)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo pill with logo inside
        logo_container = QWidget()
        logo_container.setFixedHeight(90)
        logo_container.setStyleSheet(f"background: transparent; border: 1px solid {COLORS['accent_steel']};")
        logo_outer = QVBoxLayout(logo_container)
        logo_outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_pill = GlassPanel(radius=10, bg_alpha=70)
        logo_pill.setFixedSize(200, 60)
        pill_layout = QHBoxLayout(logo_pill)
        pill_layout.setContentsMargins(12, 0, 12, 0)
        pill_layout.setSpacing(10)
        if os.path.isfile(LOGO):
            logo_img = QLabel()
            pixmap = QPixmap(LOGO).scaled(
                60, 100, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo_img.setPixmap(pixmap)
            logo_img.setStyleSheet("background: transparent;")
            pill_layout.addWidget(logo_img)
        logo_text = QLabel("SPYGLASS")
        logo_text.setFont(QFont("JetBrains Mono", 15, QFont.Weight.Bold))
        logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_text.setStyleSheet(f"color: {COLORS['accent_ice']}; letter-spacing: 3px;")
        pill_layout.addWidget(logo_text)
        logo_outer.addWidget(logo_pill)
        layout.addWidget(logo_container)

        layout.addSpacing(12)

        # Nav items matching CLI menu
        menu_items = [
            "Start Monitoring",      # 0
            "Show Current Settings", # 1
            "View Installed Apps",   # 2
            "View Running Apps",     # 3
            "Show Reports",          # 4
            "Edit Thresholds",# 5    #5 TODO: is a popUP, render as a page if triggered from sidebar
            "Exit",                  # 6
        ]
        self._nav_buttons: list[SidebarNavButton] = []
        for i, name in enumerate(menu_items):
            btn = SidebarNavButton(name)
            btn.clicked.connect(lambda checked, idx=i: self._handle_menu(idx))
            self._nav_buttons.append(btn)
            layout.addWidget(btn)
            layout.addSpacing(4)

        layout.addStretch()
        return sidebar

    def _handle_menu(self, idx: int):
        """Route sidebar clicks to pages or actions."""
        if idx == 0:
            # Start/Stop Monitoring – go to home page + toggle
            self._switch_page(0)
            self._toggle_monitoring()
        elif idx == 1:
            self._switch_page(1)
            self._refresh_settings_page()
        elif idx == 2:
            self._switch_page(2)
            self._refresh_installed_apps()
        elif idx == 3:
            self._switch_page(3)
            self._refresh_running_apps()
        elif idx == 4:
            self._switch_page(4)
            self._load_reports()
        elif idx == 5:
            self._reconfigure_thresholds()
        elif idx == 6:
            self._on_exit()

    def _switch_page(self, idx: int):
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == idx)
        self.stack.setCurrentIndex(idx)

    def _update_monitoring_label(self):
        """Keep sidebar button text in sync with monitoring state."""
        if self.spyglass.monitoring_active:
            self._nav_buttons[0].setText("Stop Monitoring")
        else:
            self._nav_buttons[0].setText("Start Monitoring")

    # ═════════════════════════════════════════════════════════════
    #  PAGE 0: HOME  (WELCOME <user> + status pill + power button)
    # ═════════════════════════════════════════════════════════════

    def resolve_display_name(self) -> str:
        """Username fallback: username → hostname → machine_id."""
        ui = self.spyglass.user_info
        if ui and isinstance(getattr(ui, 'info', None), dict):
            sys_info = ui.info.get('system', {})
            hw_info = ui.info.get('hardware', {})
            username = sys_info.get('username')
            hostname = sys_info.get('hostname')
            machine_id = hw_info.get('machine_id')
            if isinstance(username, str) and username.strip():
                return username
            if isinstance(hostname, str) and hostname.strip():
                return hostname
            if isinstance(machine_id, str) and machine_id.strip():
                return machine_id
        return "User"

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 28, 40, 28)

        # Top bar: WELCOME <user> ....... status pill
        top = QHBoxLayout()
        display_name = self.resolve_display_name().upper()
        welcome = QLabel(f"WELCOME, {display_name}")
        welcome.setFont(QFont("Inter", 26, QFont.Weight.Bold))
        welcome.setStyleSheet(f"color: {COLORS['text_primary']}; letter-spacing: 2px;")
        top.addWidget(welcome)
        top.addStretch()

        self.status_pill = StatusPill(logo_path=LOGO)
        top.addWidget(self.status_pill)
        layout.addLayout(top)

        # Center: power button
        layout.addStretch()
        center = QHBoxLayout()
        center.addStretch()
        self.power_button = PowerButton(size=260)
        self.power_button.clicked.connect(self._toggle_monitoring)
        center.addWidget(self.power_button)
        center.addStretch()
        layout.addLayout(center)
        layout.addStretch()

        return page

    # ═════════════════════════════════════════════════════════════
    #  PAGE 1: SHOW CURRENT SETTINGS
    # ═════════════════════════════════════════════════════════════

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 28, 40, 28)

        top = QHBoxLayout()
        header = QLabel("CURRENT SETTINGS")
        header.setFont(QFont("Inter UI", 24, QFont.Weight.Bold))
        header.setStyleSheet(f"letter-spacing: 4px; color: {COLORS['text_primary']};")
        top.addWidget(header)
        top.addStretch()
        self.mini_power_settings = MiniPowerIcon(48)
        top.addWidget(self.mini_power_settings)
        layout.addLayout(top)
        layout.addSpacing(16)

        self.settings_display = QTextEdit()
        self.settings_display.setReadOnly(True)
        self.settings_display.setStyleSheet(
            f"background: rgba(15,18,55,0.4); border: 1px solid {COLORS['panel_border']};"
            f" border-radius: 10px; color: {COLORS['text_secondary']}; padding: 16px;"
            f" font-family: JetBrains Mono; font-size: 13px;"
        )
        layout.addWidget(self.settings_display, 1)

        QTimer.singleShot(500, self._refresh_settings_page)
        return page

    def _refresh_settings_page(self):
        cfg = self.spyglass.config
        lines = []
        level = self.spyglass.monitoring_level or "LOW"
        status = "ACTIVE" if self.spyglass.monitoring_active else "INACTIVE"
        mode = "HIGH (App + Keystroke)" if (cfg and cfg.is_keylogger_enabled()) else "LOW (App Only)"
        lines.append(f"Monitoring Level:  {level}")
        lines.append(f"Security Mode:     {mode}")
        lines.append(f"Monitoring Status: {status}")
        lines.append("")
        if cfg:
            try:
                import json
                settings = cfg.get_config() if hasattr(cfg, 'get_config') else {}
                if settings:
                    lines.append("--- Configuration ---")
                    for k, v in settings.items():
                        if k == "thresholds":
                            lines.append(f"  {k}:")
                            for tk, tv in v.items():
                                lines.append(f"    {tk}: {tv}")
                        else:
                            lines.append(f"  {k}: {v}")
            except Exception:
                pass
        self.settings_display.setPlainText("\n".join(lines))

    # ═════════════════════════════════════════════════════════════
    #  PAGE 2: INSTALLED APPS
    # ═════════════════════════════════════════════════════════════

    def _build_installed_apps_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 28, 40, 28)

        top = QHBoxLayout()
        header = QLabel("INSTALLED APPS")
        header.setFont(QFont("Inter UI", 24, QFont.Weight.Bold))
        header.setStyleSheet(f"letter-spacing: 4px; color: {COLORS['text_primary']};")
        top.addWidget(header)
        top.addStretch()
        layout.addLayout(top)
        layout.addSpacing(16)

        self.installed_panel = InstalledAppsPanel()
        self.installed_panel.setStyleSheet("background: transparent;")
        layout.addWidget(self.installed_panel, 1)

        QTimer.singleShot(500, self._refresh_installed_apps)
        return page

    def _refresh_installed_apps(self):
        if self.spyglass.database:
            self.installed_panel.load_from_db(self.spyglass.database)

    # ═════════════════════════════════════════════════════════════
    #  PAGE 3: RUNNING APPS / ANALYTICS  (stat cards + running apps + log)
    # ═════════════════════════════════════════════════════════════

    def _build_analytics_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 28, 40, 28)

        # Header row
        top = QHBoxLayout()
        header = QLabel("RUNNING APPS")
        header.setFont(QFont("Inter UI", 24, QFont.Weight.Bold))
        header.setStyleSheet(f"letter-spacing: 4px; color: {COLORS['text_primary']};")
        top.addWidget(header)
        top.addStretch()
        self.mini_power = MiniPowerIcon(48)
        top.addWidget(self.mini_power)
        layout.addLayout(top)
        layout.addSpacing(20)

        # ── Stat cards row ──
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        self.cpu_card = GlassStatCard("CPU USAGE", "—", show_bar=True)
        self.memory_card = GlassStatCard("MEMORY", "—", show_bar=True)
        self.process_card = GlassStatCard("PROCESSES", "—")
        self.alert_card = GlassStatCard("ALERTS", "0")
        cards_row.addWidget(self.cpu_card)
        cards_row.addWidget(self.memory_card)
        cards_row.addWidget(self.process_card)
        cards_row.addWidget(self.alert_card)
        layout.addLayout(cards_row)
        layout.addSpacing(16)

        # ── Running apps + installed apps tabs ──
        apps_row = QHBoxLayout()
        apps_row.setSpacing(16)

        # Running apps panel
        self.running_panel = RunningAppsPanel()
        self.running_panel.setStyleSheet("background: transparent;")
        self.running_panel.table_widget.btn_refresh.clicked.connect(self._refresh_running_apps)
        apps_row.addWidget(self.running_panel, 1)

        layout.addLayout(apps_row, 1)

        # Activity log at bottom
        log_label = QLabel("Activity Log")
        log_label.setFont(QFont("Inter UI", 11, QFont.Weight.Bold))
        log_label.setStyleSheet(f"color: {COLORS['text_muted']}; letter-spacing: 1px;")
        layout.addWidget(log_label)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(160)
        self.log_output.append("Spyglass initialized. Waiting for monitoring to start...")
        layout.addWidget(self.log_output)

        return page

    # ═════════════════════════════════════════════════════════════
    #  PAGE 4: REPORTS  (glass table)
    # ═════════════════════════════════════════════════════════════

    def _build_reports_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 28, 40, 28)

        # Header
        top = QHBoxLayout()
        header = QLabel("REPORTS")
        header.setFont(QFont("Inter UI", 24, QFont.Weight.Bold))
        header.setStyleSheet(f"letter-spacing: 4px; color: {COLORS['text_primary']};")
        top.addWidget(header)
        top.addStretch()
        self.mini_power_reports = MiniPowerIcon(48)
        top.addWidget(self.mini_power_reports)
        layout.addLayout(top)
        layout.addSpacing(16)

        # Reports table
        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(3)
        self.reports_table.setHorizontalHeaderLabels(["File Name", "Date", "Size"])
        self.reports_table.horizontalHeader().setStretchLastSection(True)
        self.reports_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.reports_table.verticalHeader().setVisible(False)
        self.reports_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.reports_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.reports_table.setAlternatingRowColors(True)
        self.reports_table.setStyleSheet(
            f"alternate-background-color: rgba(15, 18, 55, 0.3);"
        )
        layout.addWidget(self.reports_table, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_refresh = QPushButton("Refresh")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.clicked.connect(self._load_reports)
        btn_row.addWidget(btn_refresh)

        btn_settings = QPushButton("Settings")
        btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_settings.clicked.connect(self._reconfigure_thresholds)
        btn_row.addWidget(btn_settings)
        layout.addLayout(btn_row)

        QTimer.singleShot(400, self._load_reports)
        return page

    # ── Monitoring Toggle ────────────────────────────────────────

    def _toggle_monitoring(self):
        if self.spyglass.monitoring_active:
            self.spyglass.stop_all_monitoring()
            self.power_button.set_active(False)
            self.status_pill.set_active(False)
            self.mini_power.set_active(False)
            self.mini_power_reports.set_active(False)
            self.mini_power_settings.set_active(False)
            self._update_monitoring_label()
            self._log("Monitoring stopped.")
            self._notification.show_notification("Spyglass monitoring stopped.")
        else:
            self.spyglass.start_all_monitoring()
            self._hook_alert_bridge()
            self.power_button.set_active(True)
            self.status_pill.set_active(True)
            self.mini_power.set_active(True)
            self.mini_power_reports.set_active(True)
            self.mini_power_settings.set_active(True)
            self._update_monitoring_label()
            self._log("Monitoring started.")
            self._notification.show_notification("Spyglass monitoring is now active.")

    # ── Polling ──────────────────────────────────────────────────

    def _start_polling(self):
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_stats)
        self._poll_timer.start(5000)
        QTimer.singleShot(600, self._poll_stats)

    def _poll_stats(self):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0)
            mem = psutil.virtual_memory()
            self.cpu_card.set_value(f"{cpu:.0f}%", int(cpu))
            used = mem.used / (1024**3)
            total = mem.total / (1024**3)
            self.memory_card.set_value(f"{used:.1f}/{total:.1f} GB", int(mem.percent))
            self.process_card.set_value(str(len(psutil.pids())))
        except Exception:
            pass

    def _refresh_running_apps(self):
        if self.spyglass.app_monitor:
            apps = self.spyglass.app_monitor.get_running_apps() or []
            self.running_panel.update_apps(apps)

    # ── Alerts ───────────────────────────────────────────────────

    def _hook_alert_bridge(self):
        ae = self.spyglass.alert_engine
        if not ae:
            return
        bridge = self._alert_bridge
        original = ae.raise_alert

        def patched(severity, alert_type, key, message, **kw):
            original(severity, alert_type, key, message, **kw)
            bridge.alert_raised.emit(severity, alert_type, message)

        ae.raise_alert = patched

    def _on_alert_raised(self, severity, alert_type, message):
        color = SEVERITY_COLORS.get(severity.upper(), COLORS["text_primary"])
        self._log(f'<span style="color:{color};font-weight:bold;">[{severity}]</span> {alert_type}: {message}')
        self._alert_count += 1
        self.alert_card.set_value(str(self._alert_count), color=color)

    # ── Reports ──────────────────────────────────────────────────

    def _load_reports(self):
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Reports")
        self.reports_table.setRowCount(0)
        if not os.path.isdir(reports_dir):
            return
        files = sorted(os.listdir(reports_dir))
        self.reports_table.setRowCount(len(files))
        for i, f in enumerate(files):
            fp = os.path.join(reports_dir, f)
            size = os.path.getsize(fp) if os.path.isfile(fp) else 0
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d %H:%M")
            size_str = f"{size / 1024:.1f} KB" if size > 1024 else f"{size} B"
            self.reports_table.setItem(i, 0, QTableWidgetItem(f))
            self.reports_table.setItem(i, 1, QTableWidgetItem(mtime))
            self.reports_table.setItem(i, 2, QTableWidgetItem(size_str))

    # ── Settings / Thresholds ────────────────────────────────────

    def _reconfigure_thresholds(self):
        dialog = ThresholdWindow(
            monitoring_level=self.spyglass.monitoring_level or "LOW",
            parent=self,
        )
        if dialog.exec():
            thresholds = dialog.get_thresholds()
            if self.spyglass.consent:
                self.spyglass.consent.thresholds = thresholds
            try:
                uid = ""
                if self.spyglass.user_info:
                    uid = self.spyglass.user_info.info.get("hardware", {}).get("machine_id", "")
                from db.database import insertIntoThresholdTable
                for name, sd in thresholds.items():
                    for sev, val in sd.items():
                        insertIntoThresholdTable(userID=uid, thresholdType="security",
                                                 settingName=f"{name}_{sev}", settingValue=str(val))
            except Exception as e:
                logging.error(f"Failed to persist thresholds: {e}")
            if self.spyglass.config:
                self.spyglass.config.set_setting("thresholds", thresholds)
                self.spyglass.config.save_config()
            if self.spyglass.alert_engine:
                self.spyglass.alert_engine.update_thresholds(thresholds)
            self._log("Thresholds reconfigured.")

    # ── Helpers ──────────────────────────────────────────────────

    def _log(self, msg: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_output.append(
            f'<span style="color:{COLORS["text_muted"]};">[{ts}]</span> {msg}'
        )

    def _on_exit(self):
        reply = QMessageBox.question(
            self, "Exit Spyglass", "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.spyglass.monitoring_active:
                self.spyglass.stop_all_monitoring()
            self.close()

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Exit Spyglass",
            "Are you sure you want to exit Spyglass?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.spyglass.monitoring_active:
                self.spyglass.stop_all_monitoring()
            self.spyglass.cleanup()
            event.accept()
        else:
            event.ignore()
