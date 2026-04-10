"""Spyglass theme system — darker, sharper, metallic glass."""

import os as _os

LOGO = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
    "logo", "spyglass_logo.png",
).replace("\\", "/")

COLORS = {
    # Core background
    "bg_0": "#05070f",
    "bg_1": "#04184f",
    "bg_2": "#2d3244",
    "bg_3": "#313e72",

    # Surface + glass
    "panel_fill": "rgba(10, 14, 28, 0.72)",
    "panel_fill_soft": "rgba(14, 18, 34, 0.58)",
    "panel_hover": "rgba(255, 255, 255, 0.035)",
    "panel_border": "rgba(210, 225, 255, 0.12)",
    "panel_border_strong": "rgba(230, 240, 255, 0.18)",
    "panel_highlight": "rgba(255, 255, 255, 0.08)",

    # Typography
    "text_primary": "#F5F7FF",
    "text_secondary": "#A7B0C5",
    "text_muted": "#68718A",

    # New accent system
    "accent_ice": "#EAF2FF",
    "accent_steel": "#9FB3D9",
    "accent_blue": "#7C8DFF",
    "accent_line": "rgba(124, 141, 255, 0.42)",
    "accent_glow": "rgba(210, 225, 255, 0.10)",

    # State colors
    "accent_red": "#FF5C7A",
    "accent_green": "#59D38C",
    "severity_low": "#8FB4FF",
    "severity_medium": "#F2C94C",
    "severity_high": "#F2994A",
    "severity_critical": "#EB5757",

    "success": "#59D38C",
    "warning": "#F2C94C",
    "error": "#FF7A7A",
    "critical": "#C93C3C",
    "transparent": "transparent",
}

SEVERITY_COLORS = {
    "LOW": COLORS["severity_low"],
    "MEDIUM": COLORS["severity_medium"],
    "HIGH": COLORS["severity_high"],
    "CRITICAL": COLORS["severity_critical"],
}

BG_GRADIENT_CSS = """
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0   #05070f,
        stop:0.28 #0a1020,
        stop:0.62 #0f1630,
        stop:1.0 #151d3d
    );
"""

GLOBAL_STYLESHEET = f"""
    QMainWindow, QDialog {{
        {BG_GRADIENT_CSS}
        color: {COLORS['text_primary']};
        font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    }}

    QWidget {{
        color: {COLORS['text_primary']};
        font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
        background: transparent;
    }}

    QLabel {{
        color: {COLORS['text_primary']};
        background: transparent;
    }}

    QPushButton {{
        background-color: {COLORS['panel_fill_soft']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['panel_border']};
        border-radius: 10px;
        padding: 10px 18px;
        font-size: 13px;
        font-weight: 600;
    }}

    QPushButton:hover {{
        background-color: {COLORS['panel_hover']};
        border: 1px solid {COLORS['panel_border_strong']};
    }}

    QPushButton:pressed {{
        background-color: rgba(255,255,255,0.02);
    }}

    QPushButton#accent {{
        background-color: rgba(124, 141, 255, 0.16);
        border: 1px solid rgba(124, 141, 255, 0.30);
    }}

    QPushButton#accent:hover {{
        background-color: rgba(124, 141, 255, 0.22);
    }}

    QPushButton#danger {{
        background-color: rgba(255, 92, 122, 0.14);
        border: 1px solid rgba(255, 92, 122, 0.24);
    }}

    QPushButton#danger:hover {{
        background-color: rgba(255, 92, 122, 0.20);
    }}
    
    QRadioButton, QCheckBox {{
        color: {COLORS['text_primary']};
        spacing: 8px;
        font-size: 14px;
        background: transparent;
    }}
    QRadioButton::indicator {{
        width: 20px;
        height: 20px;
        border: 2px solid {COLORS['panel_border']};
        border-radius: 10px;
        background: rgba(10, 15, 40, 0.6);
    }}
    QRadioButton::indicator:hover {{
        border: 2px solid {COLORS['accent_blue']};
    }}
    QRadioButton::indicator:checked {{
        border: 2px solid {COLORS['accent_ice']};
        image: url({LOGO});
    }}

    QLineEdit, QSpinBox, QComboBox {{
        background-color: rgba(255,255,255,0.035);
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['panel_border']};
        border-radius: 10px;
        padding: 10px 12px;
        font-size: 13px;
    }}

    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 1px solid rgba(159, 179, 217, 0.42);
    }}

    QTableWidget {{
        background-color: rgba(255,255,255,0.02);
        alternate-background-color: rgba(255,255,255,0.035);
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['panel_border']};
        border-radius: 12px;
        gridline-color: rgba(255,255,255,0.04);
        selection-background-color: rgba(255,255,255,0.08);
    }}

    QTableWidget::item {{
        padding: 8px;
        border: none;
    }}

    QHeaderView::section {{
        background-color: rgba(255,255,255,0.025);
        color: {COLORS['accent_ice']};
        border: none;
        border-bottom: 1px solid {COLORS['panel_border']};
        padding: 10px 12px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}

    QTextEdit {{
        background-color: rgba(255,255,255,0.025);
        color: {COLORS['text_secondary']};
        border: 1px solid {COLORS['panel_border']};
        border-radius: 12px;
        font-family: 'JetBrains Mono', 'Consolas', monospace;
        font-size: 12px;
        padding: 10px;
    }}

    QProgressBar {{
        background-color: rgba(255,255,255,0.03);
        border: none;
        border-radius: 4px;
        text-align: center;
    }}

    QProgressBar::chunk {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(234,242,255,0.70),
            stop:1 rgba(124,141,255,0.85)
        );
        border-radius: 4px;
    }}
"""