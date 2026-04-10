"""Reusable app-table widget — Glass UI design."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from gui.styles import COLORS
from gui.glass_widgets import GlassPanel


class AppTableWidget(QWidget):
    """Sortable, filterable table for application data — glass themed."""

    def __init__(self, title: str, columns: list[str], parent=None):
        super().__init__(parent)
        self.columns = columns
        self._all_rows: list[list[str]] = []
        self.setStyleSheet("background: transparent;")
        self.build_ui(title)

    def build_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header bar
        header_bar = QHBoxLayout()
        lbl = QLabel(title)
        lbl.setFont(QFont("JetBrains Mono", 12, QFont.Weight.Bold))
        lbl.setStyleSheet(
            f"color: {COLORS['accent_steel']}; background: transparent; letter-spacing: 2px;"
        )
        header_bar.addWidget(lbl)
        header_bar.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter...")
        self.search_input.setMaximumWidth(250)
        self.search_input.setStyleSheet(
            f"""
            QLineEdit {{
                background: rgba(255,255,255,0.035);
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['panel_border']};
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['panel_border_strong']};
            }}
            """
        )
        self.search_input.textChanged.connect(self.apply_filter)
        header_bar.addWidget(self.search_input)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.setStyleSheet(
            f"""
            QPushButton {{
                background: {COLORS['panel_fill_soft']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['panel_border']};
                border-radius: 10px;
                padding: 8px 18px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {COLORS['panel_hover']};
                color: {COLORS['text_primary']};
                border-color: {COLORS['panel_border_strong']};
            }}
            """
        )
        header_bar.addWidget(self.btn_refresh)

        layout.addLayout(header_bar)

        # Count label
        self.count_label = QLabel("0 items")
        self.count_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px; background: transparent;"
        )
        layout.addWidget(self.count_label)

        # Table — glass styling
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.table.setStyleSheet(
            f"""
            QTableWidget {{
                background: rgba(255,255,255,0.02);
                alternate-background-color: rgba(255,255,255,0.035);
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['panel_border']};
                border-radius: 12px;
                gridline-color: rgba(255,255,255,0.04);
            }}
            QHeaderView::section {{
                background: rgba(255,255,255,0.02);
                color: {COLORS['accent_ice']};
                border: none;
                border-bottom: 1px solid {COLORS['panel_border']};
                padding: 8px 10px;
                font-weight: 700;
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
            }}
            QTableWidget::item:selected {{
                background: rgba(255,255,255,0.08);
                color: {COLORS['text_primary']};
            }}
            """
        )
        layout.addWidget(self.table, 1)

    def set_data(self, rows: list[list[str]]):
        self._all_rows = rows
        self.apply_filter(self.search_input.text())

    def apply_filter(self, text: str):
        text = text.lower()
        filtered = [
            row for row in self._all_rows
            if not text or any(text in str(cell).lower() for cell in row)
        ]
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(filtered))
        for r, row in enumerate(filtered):
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.setSortingEnabled(True)
        self.count_label.setText(f"{len(filtered)} item(s)")


class InstalledAppsPanel(GlassPanel):
    """Panel showing apps from the database — glass panel."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        self.table_widget = AppTableWidget(
            "Installed Applications",
            ["Application Name", "Vendor", "Executable Path"]
        )
        layout.addWidget(self.table_widget)

    def load_from_db(self, database):
        if not database or not database.connection:
            return
        try:
            cursor = database.connection.cursor()
            cursor.execute("""
                SELECT appName, vendor, executablePath
                FROM application
                ORDER BY appName COLLATE NOCASE ASC
            """)
            rows = [[name, vendor or "Unknown", path] for name, vendor, path in cursor.fetchall()]
            cursor.close()
            self.table_widget.set_data(rows)
        except Exception:
            pass


class RunningAppsPanel(GlassPanel):
    """Panel showing currently running processes — glass panel."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        self.table_widget = AppTableWidget(
            "Running Applications",
            ["Name", "PID", "Memory (MB)", "CPU %", "Window Title"]
        )
        layout.addWidget(self.table_widget)

    def update_apps(self, apps: list):
        rows = []
        for app in sorted(apps, key=lambda x: x.get("memory_mb", 0), reverse=True):
            rows.append([
                app.get("name", ""),
                str(app.get("pid", "")),
                f"{app.get('memory_mb', 0):.1f}",
                f"{app.get('cpu_percent', 0):.1f}",
                app.get("window_title", ""),
            ])
        self.table_widget.set_data(rows)
