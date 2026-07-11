"""
popup.py
Base class for every floating, Omarchy/Zen-style popup window in
VoidBrowser (launcher, URL bar, tab switcher, bookmarks, history,
downloads, settings). Popups are frameless, centered over the parent
window, closed on Escape or focus loss, and themed via QSS.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGraphicsOpacityEffect


class FloatingPopup(QWidget):
    """A frameless, centered, semi-transparent floating window."""

    def __init__(self, parent: QWidget | None, width_ratio: float = 0.5,
                 height: int | None = None, anchor: str = "center") -> None:
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("floatingPopup")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._width_ratio = width_ratio
        self._fixed_height = height
        self._anchor = anchor

        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(16, 16, 16, 16)
        self.layout_.setSpacing(8)

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0.0)

    def _target_geometry(self) -> tuple[int, int, int, int]:
        host = self.parentWidget()
        if host is not None:
            geo = host.geometry()
            top_left = host.mapToGlobal(geo.topLeft())
            base_x, base_y, base_w, base_h = top_left.x(), top_left.y(), geo.width(), geo.height()
        else:
            screen = QGuiApplication.primaryScreen().geometry()
            base_x, base_y, base_w, base_h = screen.x(), screen.y(), screen.width(), screen.height()

        width = int(base_w * self._width_ratio)
        height = self._fixed_height or int(base_h * 0.6)

        if self._anchor == "center":
            x = base_x + (base_w - width) // 2
            y = base_y + (base_h - height) // 3
        else:  # "top"
            x = base_x + (base_w - width) // 2
            y = base_y + 80
        return x, y, width, height

    def show_animated(self) -> None:
        x, y, w, h = self._target_geometry()
        self.setGeometry(x, y, w, h)
        self.show()
        self.raise_()
        self.activateWindow()

        anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        anim.setDuration(120)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self._show_anim = anim  # keep a reference alive

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)
