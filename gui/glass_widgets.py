"""Glass UI widget primitives for Spyglass GUI.

Provides:
  - GlassPanel: frosted semi-transparent container with rounded corners
  - GradientBackground: full-window gradient mixin
  - PowerButton: large circular glass toggle (red OFF / green ON)
  - StatusPill: rounded status badge (like the wireframe monitoring banner)
  - GlassSidebar: sidebar with glass effect and rounded right corners
"""

import math
from PyQt6.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QSize
from PyQt6.QtGui import (
    QPainter, QColor, QLinearGradient, QRadialGradient, QPen,
    QFont, QBrush, QPainterPath, QConicalGradient, QPixmap,
)

from gui.styles import COLORS


# ═══════════════════════════════════════════════════════════════════
#  Gradient Background Mixin
# ═══════════════════════════════════════════════════════════════════

class GradientBackground:
    """Mixin: override paintEvent to draw the deep-blue gradient bg."""

    def paint_gradient_bg(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        w, h = rect.width(), rect.height()

        base = QLinearGradient(0, 0, w, h)
        base.setColorAt(0.0, QColor(COLORS["bg_0"]))
        base.setColorAt(0.25, QColor(COLORS["bg_1"]))
        base.setColorAt(0.62, QColor(COLORS["bg_2"]))
        base.setColorAt(1.0, QColor(COLORS["bg_3"]))
        p.fillRect(rect, base)

        # restrained metallic light, top-right
        g1 = QRadialGradient(QPointF(w * 0.82, h * 0.10), w * 0.32)
        g1.setColorAt(0.0, QColor(220, 232, 255, 24))
        g1.setColorAt(0.45, QColor(124, 141, 255, 12))
        g1.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(rect, g1)

        # lower ambient bloom
        g2 = QRadialGradient(QPointF(w * 0.55, h * 1.02), w * 0.48)
        g2.setColorAt(0.0, QColor(180, 205, 255, 18))
        g2.setColorAt(0.4, QColor(124, 141, 255, 10))
        g2.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(rect, g2)

        p.end()

# ═══════════════════════════════════════════════════════════════════
#  Glass Panel
# ═══════════════════════════════════════════════════════════════════

class GlassPanel(QFrame):
    """Frosted-glass container with semi-transparent bg and glow border."""

    def __init__(self, radius: int = 10, bg_alpha: int = 60, parent=None):
        super().__init__(parent)
        self._radius = radius
        self._bg_alpha = bg_alpha
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        path = QPainterPath()
        path.addRoundedRect(rect, self._radius, self._radius)

        p.fillPath(path, QColor(10, 14, 28, self._bg_alpha))

        sheen = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.top() + 80))
        sheen.setColorAt(0, QColor(255, 255, 255, 16))
        sheen.setColorAt(0.35, QColor(255, 255, 255, 6))
        sheen.setColorAt(1, QColor(255, 255, 255, 0))
        p.fillPath(path, sheen)

        p.setPen(QPen(QColor(210, 225, 255, 30), 1.0))
        p.drawRoundedRect(rect, self._radius, self._radius)
        p.end()
       


# ═══════════════════════════════════════════════════════════════════
#  Glass Sidebar (rounded right corners, like wireframe)
# ═══════════════════════════════════════════════════════════════════

class GlassSidebar(QFrame):
    """Sidebar panel with glass effect – rounded on the right side only."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())
        r = 18

        path = QPainterPath()
        path.moveTo(rect.left(), rect.top())
        path.lineTo(rect.right() - r, rect.top())
        path.arcTo(QRectF(rect.right() - 2 * r, rect.top(), 2 * r, 2 * r), 90, -90)
        path.lineTo(rect.right(), rect.bottom() - r)
        path.arcTo(QRectF(rect.right() - 2 * r, rect.bottom() - 2 * r, 2 * r, 2 * r), 0, -90)
        path.lineTo(rect.left(), rect.bottom())
        path.closeSubpath()

        # Base fill: deep blue glass matching wireframe
        base_grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        base_grad.setColorAt(0.0,  QColor(8, 14, 50, 180))    # deep navy top
        base_grad.setColorAt(0.4,  QColor(12, 22, 72, 170))   # mid blue
        base_grad.setColorAt(0.8,  QColor(10, 18, 60, 165))   # stays deep
        base_grad.setColorAt(1.0,  QColor(6, 12, 45, 175))    # bottom
        p.fillPath(path, base_grad)

        # Subtle top-left sheen (very restrained)
        top_sheen = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.top() + 100))
        top_sheen.setColorAt(0, QColor(160, 185, 255, 14))
        top_sheen.setColorAt(0.3, QColor(120, 150, 230, 6))
        top_sheen.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillPath(path, top_sheen)

        # Right edge: pink/violet accent (wireframe signature)
        edge_iri = QLinearGradient(QPointF(rect.right() - 30, rect.top()), QPointF(rect.right(), rect.center().y()))
        edge_iri.setColorAt(0.0, QColor(0, 0, 0, 0))
        edge_iri.setColorAt(0.5, QColor(160, 100, 220, 20))   # violet
        edge_iri.setColorAt(0.8, QColor(200, 120, 180, 22))   # pink
        edge_iri.setColorAt(1.0, QColor(180, 140, 255, 12))   # fade
        p.fillPath(path, edge_iri)

        # Bottom-left cyan glow
        cyan_glow = QRadialGradient(QPointF(rect.left() + 30, rect.bottom() - 20), 80)
        cyan_glow.setColorAt(0.0, QColor(60, 200, 240, 28))
        cyan_glow.setColorAt(0.5, QColor(40, 160, 220, 12))
        cyan_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillPath(path, cyan_glow)

        p.setPen(QPen(QColor(210, 225, 255, 55), 1.2))
        p.drawPath(path)

        p.end()

# ═══════════════════════════════════════════════════════════════════
#  Power Button (large circular glass toggle)
# ═══════════════════════════════════════════════════════════════════

class PowerButton(QWidget):
    """Large glass power button that toggles red (OFF) ↔ green (ON)."""

    clicked = pyqtSignal()

    def __init__(self, size: int = 200, parent=None):
        super().__init__(parent)
        self._size = size
        self._active = False
        self._hovered = False
        # Extra padding so glow doesn't clip
        pad = int(size * 0.18)
        self.setFixedSize(size + pad * 2, size + pad * 2)
        self._pad = pad
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def is_active(self) -> bool:
        return self._active

    def set_active(self, active: bool):
        self._active = active
        self.update()

    def toggle(self):
        self._active = not self._active
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    #colour logic
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self._size
        pad = self._pad
        cx, cy = pad + s / 2, pad + s / 2
        r = s * 0.45  # main radius

        # Choose colour
        if self._active:
            ring_color = QColor(COLORS["accent_green"])
            glow_color = QColor(68, 207, 108, 50)
            icon_color = QColor(100, 200, 130, 160)
        else:
            ring_color = QColor(COLORS["accent_red"])
            glow_color = QColor(196, 69, 105, 50)
            icon_color = QColor(196, 100, 130, 160)

        # Hover: ice accent tint
        if self._hovered:
            ice = QColor(COLORS["accent_ice"])
            ring_color = ice
            glow_color = QColor(ice.red(), ice.green(), ice.blue(), 55)
            icon_color = QColor(ice.red(), ice.green(), ice.blue(), 160)

        # Outer glow (radial ellipse, not fillRect)
        glow = QRadialGradient(QPointF(cx, cy), r * 1.3)
        glow.setColorAt(0.5, glow_color)
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(cx, cy), r * 1.3, r * 2.5)

        # Glass sphere
        sphere_grad = QRadialGradient(QPointF(cx, cy * 0.9), r)
        sphere_grad.setColorAt(0.0, QColor(40, 50, 110, 120))
        sphere_grad.setColorAt(0.6, QColor(20, 25, 70, 100))
        sphere_grad.setColorAt(1.0, QColor(10, 12, 50, 80))
        p.setBrush(QBrush(sphere_grad))
        p.setPen(QPen(QColor(120, 140, 220, 50), 1.5))
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Highlight crescent
        hl_grad = QRadialGradient(QPointF(cx - r * 0.25, cy - r * 0.3), r * 0.8)
        hl_grad.setColorAt(0.0, QColor(255, 255, 255, 22))
        hl_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(hl_grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), r * 0.95, r * 0.95)

        # Concentric rings (power icon outer ring)
        ring_pen = QPen(ring_color, 3)
        ring_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(ring_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r * 0.65, r * 0.65)
        p.drawEllipse(QPointF(cx, cy), r * 0.45, r * 0.45)

        # Power icon: arc (open at top)
        icon_pen = QPen(icon_color, 4)
        icon_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(icon_pen)
        arc_r = r * 0.32
        arc_rect = QRectF(cx - arc_r, cy - arc_r, arc_r * 2, arc_r * 2)
        p.drawArc(arc_rect, 120 * 16, 300 * 16)  # open at top

        # Power icon: vertical line
        p.drawLine(QPointF(cx, cy - arc_r - 4), QPointF(cx, cy - arc_r * 0.15))

        p.end()


# ═══════════════════════════════════════════════════════════════════
#  Status Pill (monitoring status banner)
# ═══════════════════════════════════════════════════════════════════

class StatusPill(QFrame):
    """Pill status indicator matching the wireframe banner."""

    def __init__(self, logo_path: str = "", parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        self.setMinimumWidth(280)
        self.setMaximumWidth(380)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._active = False
        self._text = "SPYGLASS is not watching."

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 20, 0)
        layout.setSpacing(12)

        self._icon_label = QLabel()
        self._icon_label.setFixedSize(32, 32)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("background: transparent;")
        import os
        if logo_path and os.path.isfile(logo_path):
            pixmap = QPixmap(logo_path).scaled(
                28, 28, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._icon_label.setPixmap(pixmap)
        else:
            self._icon_label.setText("⊙")
            self._icon_label.setFont(QFont("Gruppo", 18))
        layout.addWidget(self._icon_label)

        self._text_label = QLabel(self._text)
        self._text_label.setFont(QFont("Gruppo", 11))
        self._text_label.setWordWrap(True)
        self._text_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self._text_label)

    def set_active(self, active: bool):
        self._active = active
        if active:
            self._text_label.setText("SPYGLASS is now watching.")
            self._text_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        else:
            self._text_label.setText("SPYGLASS is no longer watching.")
            self._text_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        radius = 14

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        if self._active:
            fill = QColor(20, 50, 80, 140)
            border = QColor(77, 208, 225, 80)
        else:
            fill = QColor(60, 30, 50, 130)
            border = QColor(196, 69, 105, 70)

        p.fillPath(path, fill)

        # Highlight
        hl = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.bottom()))
        hl.setColorAt(0, QColor(255, 255, 255, 10))
        hl.setColorAt(1, QColor(255, 255, 255, 0))
        p.fillPath(path, hl)

        p.setPen(QPen(border, 1.2))
        p.drawRoundedRect(rect, radius, radius)
        p.end()


# ═══════════════════════════════════════════════════════════════════
#  Stat Card (glass card for CPU / Memory / etc.)
# ═══════════════════════════════════════════════════════════════════

class GlassStatCard(GlassPanel):
    """Stat card: title + large value + optional progress bar inside glass panel."""

    def __init__(self, title: str, value: str = "—", show_bar: bool = False, parent=None):
        super().__init__(radius=10, bg_alpha=60, parent=parent)
        self.setMinimumHeight(100)
        self.setMinimumWidth(160)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Gruppo", 10))
        self.title_label.setStyleSheet(f"color: {COLORS['text_muted']}; letter-spacing: 1px;")
        layout.addWidget(self.title_label)

        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Gruppo", 22, QFont.Weight.Bold))
        layout.addWidget(self.value_label)

        from PyQt6.QtWidgets import QProgressBar
        self.bar = None
        if show_bar:
            self.bar = QProgressBar()
            self.bar.setMaximumHeight(6)
            self.bar.setTextVisible(False)
            layout.addWidget(self.bar)

    def set_value(self, value: str, bar_value: int = None, color: str = None):
        self.value_label.setText(value)
        if color:
            self.value_label.setStyleSheet(f"color: {color};")
        if self.bar is not None and bar_value is not None:
            self.bar.setValue(bar_value)
            if bar_value > 90:
                chunk_color = COLORS["critical"]
            elif bar_value > 75:
                chunk_color = COLORS["warning"]
            else:
                chunk_color = COLORS["accent_steel"]
            self.bar.setStyleSheet(
                f"QProgressBar::chunk {{ background-color: {chunk_color}; border-radius: 3px; }}"
                f"QProgressBar {{ background: rgba(10,15,40,0.5); border: none; border-radius: 3px; }}"
            )
