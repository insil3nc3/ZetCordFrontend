from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QEvent, QPropertyAnimation, QEasingCurve, pyqtProperty, Qt
from PyQt6.QtGui import QColor, QCursor, QFont


class AnimatedButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._color = QColor("gray")
        self._hover_color = QColor("#9B4DCA")
        self._pressed_color = QColor("#2C1D6A")
        self._default_color = QColor("gray")

        self.setStyleSheet("text-decoration: underline; background-color: transparent; border: none;")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFont(QFont('Inter', 14, QFont.Weight.ExtraBold))
        self.setFixedWidth(250)

        self._animation = QPropertyAnimation(self, b"textColor", self)
        self._animation.setDuration(300)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.installEventFilter(self)
        self.set_text_color(self._default_color)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Enter:
            self._start_animation(self._hover_color)
        elif event.type() == QEvent.Type.Leave:
            self._start_animation(self._default_color)
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        self._start_animation(self._pressed_color)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # Проверим, находится ли курсор всё ещё над кнопкой
        if self.rect().contains(event.pos()):
            self._start_animation(self._hover_color)
        else:
            self._start_animation(self._default_color)
        super().mouseReleaseEvent(event)

    def _start_animation(self, target_color):
        self._animation.stop()
        self._animation.setStartValue(self._color)
        self._animation.setEndValue(target_color)
        self._animation.start()

    def get_text_color(self):
        return self._color

    def set_text_color(self, color):
        if isinstance(color, QColor):
            self._color = color
            self.setStyleSheet(f"""
                color: {color.name()};
                text-decoration: underline;
                background-color: transparent;
                border: none;
            """)

    textColor = pyqtProperty(QColor, fget=get_text_color, fset=set_text_color)