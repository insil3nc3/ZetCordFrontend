from PyQt6.QtCore import pyqtProperty, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget


class ColorAnimatableWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bg_color = QColor("#1f1b24")

    def get_bg_color(self):
        return self._bg_color

    def set_bg_color(self, color):
        self._bg_color = color
        self.setStyleSheet(f"background-color: {color.name()}; border-radius: 10px;")

    bg_color = pyqtProperty(QColor, fget=get_bg_color, fset=set_bg_color)
