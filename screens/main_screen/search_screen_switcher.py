from PyQt6.QtWidgets import QWidget, QStackedLayout, QStackedWidget, QVBoxLayout
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QParallelAnimationGroup, QObject

from screens.main_screen.transition import animate_transition


class AnimatedSwitcher(QObject):
    def __init__(self, container: QWidget, duration=500):
        super().__init__()
        self.container = container
        self.stack = QStackedWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
        self.duration = duration
        self.view_stack = []

    def add_widget(self, widget: QWidget):
        self.stack.addWidget(widget)

    def set_current_index(self, index: int):
        self.stack.setCurrentIndex(index)


    def slide_to_index(self, index: int, direction="up"):
        is_back = direction == "down"
        animate_transition(self, index, is_back=is_back)
