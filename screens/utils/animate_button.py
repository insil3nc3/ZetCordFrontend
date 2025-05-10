from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QEvent, QPropertyAnimation, pyqtProperty, QEasingCurve, QObject, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QCursor
from PyQt6.QtCore import Qt

class StyledAnimatedButton(QPushButton):
    def __init__(self, text="", parent=None, def_color=None):
        super().__init__(text, parent)

        # Основные стили
        if not def_color:
            default_color = "#333333"
        else:
            default_color = def_color
        self._default_bg = QColor(default_color)
        self._hover_bg = QColor("#9B4DCA")
        self._pressed_bg = QColor("#2C1D6A")

        self._default_text = QColor("#9B4DCA")
        self._hover_text = QColor("#FFFFFF")
        self._pressed_text = QColor("#E1A9FF")

        self._default_border = QColor("transparent")
        self._hover_border = QColor("#9B4DCA")
        self._pressed_border = QColor("#9B4DCA")

        # Текущие значения
        self._bg_color = self._default_bg
        self._text_color = self._default_text
        self._border_color = self._default_border

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFont(QFont('Inter', 18, QFont.Weight.Bold))
        self.setFixedHeight(50)
        self.setFixedWidth(300)

        self._bg_anim = QPropertyAnimation(self, b"bgColor", self)
        self._text_anim = QPropertyAnimation(self, b"textColor", self)
        self._border_anim = QPropertyAnimation(self, b"borderColor", self)

        for anim in (self._bg_anim, self._text_anim, self._border_anim):
            anim.setDuration(300)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.installEventFilter(self)
        self.update_stylesheet()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Enter:
            self._animate_to(self._hover_bg, self._hover_text, self._hover_border)
        elif event.type() == QEvent.Type.Leave:
            self._animate_to(self._default_bg, self._default_text, self._default_border)
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        # Быстрая анимация "нажатия"
        self._animate_to(
            self._pressed_bg,
            self._pressed_text,
            self._pressed_border,
            duration=100  # Ускоренная анимация
        )
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.rect().contains(event.pos()):
            # Если курсор всё ещё над кнопкой — плавно вернёмся в "hover"
            self._animate_to(
                self._hover_bg,
                self._hover_text,
                self._hover_border,
                duration=300
            )
        else:
            # Если ушёл — вернёмся в обычный стиль
            self._animate_to(
                self._default_bg,
                self._default_text,
                self._default_border,
                duration=300
            )
        super().mouseReleaseEvent(event)

    def _animate_to(self, bg, text, border, duration=300):
        def start(anim, attr_name, target_color):
            anim.stop()
            anim.setDuration(duration)
            anim.setStartValue(getattr(self, attr_name))
            anim.setEndValue(target_color)
            anim.start()

        start(self._bg_anim, "_bg_color", bg)
        start(self._text_anim, "_text_color", text)
        start(self._border_anim, "_border_color", border)

        # Обновляем целевые значения
        self._target_bg = bg
        self._target_text = text
        self._target_border = border

    def update_stylesheet(self):
        border_style = (
            "none" if self._border_color.alpha() == 0
            else f"2px solid {self._border_color.name()}"
        )

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._bg_color.name()};
                color: {self._text_color.name()};
                border: {border_style};
                font-size: 18px;
                padding: 10px;
                border-radius: 6px;
            }}
        """)

    # Свойства
    def get_bg_color(self): return self._bg_color
    def set_bg_color(self, color):
        self._bg_color = color
        self.update_stylesheet()
    bgColor = pyqtProperty(QColor, fget=get_bg_color, fset=set_bg_color)

    def get_text_color(self): return self._text_color
    def set_text_color(self, color):
        self._text_color = color
        self.update_stylesheet()
    textColor = pyqtProperty(QColor, fget=get_text_color, fset=set_text_color)

    def get_border_color(self): return self._border_color
    def set_border_color(self, color):
        self._border_color = color
        self.update_stylesheet()
    borderColor = pyqtProperty(QColor, fget=get_border_color, fset=set_border_color)
