from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QEvent, QPropertyAnimation, pyqtProperty, QEasingCurve, QObject, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QCursor
from PyQt6.QtCore import Qt

class StyledAnimatedButton(QPushButton):
    def __init__(self, text="", parent=None, def_color="#333333", btn_style="default", width=300, height=50, font_size=18, border_radius=6):
        super().__init__(text, parent)

        self.width = width
        self.height = height
        self._style = btn_style
        self.def_color = def_color
        self.font_size = font_size
        self.border_radius = border_radius

        if self._style == "default":
            self._default_bg = QColor(self.def_color)
            self._hover_bg = QColor("#1c1c1c")        # Фиолетовый
            self._pressed_bg = QColor("transparent")  # Прозрачный фиолетовый оттенок

            self._default_text = QColor("white")
            self._hover_text = QColor("white")
            self._pressed_text = QColor("white")

            self._default_border = QColor(self.def_color)
            self._hover_border = QColor("#9B4DCA")
            self._pressed_border = QColor("#9B4DCA")

        elif self._style == "positive":
            self._default_bg = QColor("#3ba55d")  # Основной зелёный — яркий, дружелюбный
            self._hover_bg = QColor("#2e8a4e")  # Тёмнее при наведении
            self._pressed_bg = QColor("#247343")  # Ещё темнее при зажатии

            self._default_text = QColor("#84e1a0")
            self._hover_text = QColor("#FFFFFF")
            self._pressed_text = QColor("#b2ffcc")

            self._default_border = QColor("#3ba55d")
            self._hover_border = QColor("#2e8a4e")
            self._pressed_border = QColor("#247343")

        elif self._style == "negative":
            self._default_bg = QColor("#ed4245")  # Яркий красный
            self._hover_bg = QColor("#c53b3e")  # Тёмнее при наведении
            self._pressed_bg = QColor("#a83235")  # Ещё темнее при зажатии

            self._default_text = QColor("#ff9999")
            self._hover_text = QColor("#FFFFFF")
            self._pressed_text = QColor("#ffcccc")

            self._default_border = QColor("#ed4245")
            self._hover_border = QColor("#c53b3e")
            self._pressed_border = QColor("#a83235")

        else:
            raise ValueError("btn_style должен быть 'default', 'positive' или 'negative'")

        self._bg_color = self._default_bg
        self._text_color = self._default_text
        self._border_color = self._default_border

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFont(QFont('Inter', self.font_size, QFont.Weight.Bold))
        self.setFixedHeight(self.height)

        self.setFixedWidth(self.width)

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
        self._animate_to(self._pressed_bg, self._pressed_text, self._pressed_border, duration=100)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.rect().contains(event.pos()):
            self._animate_to(self._hover_bg, self._hover_text, self._hover_border, duration=300)
        else:
            self._animate_to(self._default_bg, self._default_text, self._default_border, duration=300)
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
                font-size: {self.font_size}px;
                padding: 5px;
                border-radius: {self.border_radius}px;
            }}
        """)

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

    def edit_text(self, text):
        self.setText(text)

    # Внутри StyledAnimatedButton (или через наследование от него):
    def update_style(self, new_style):
        self.apply_style(new_style)

    def apply_style(self, style):
        self._style = style

        if self._style == "default":
            self._default_bg = QColor(self.def_color)
            self._hover_bg = QColor("#1c1c1c")
            self._pressed_bg = QColor("transparent")

            self._default_text = QColor("white")
            self._hover_text = QColor("white")
            self._pressed_text = QColor("white")

            self._default_border = QColor(self.def_color)
            self._hover_border = QColor("#9B4DCA")
            self._pressed_border = QColor("#9B4DCA")

        elif self._style == "positive":
            self._default_bg = QColor("#3ba55d")
            self._hover_bg = QColor("#2e8a4e")
            self._pressed_bg = QColor("#247343")

            self._default_text = QColor("#84e1a0")
            self._hover_text = QColor("#FFFFFF")
            self._pressed_text = QColor("#b2ffcc")

            self._default_border = QColor("#3ba55d")
            self._hover_border = QColor("#2e8a4e")
            self._pressed_border = QColor("#247343")

        elif self._style == "negative":
            self._default_bg = QColor("#ed4245")
            self._hover_bg = QColor("#c53b3e")
            self._pressed_bg = QColor("#a83235")

            self._default_text = QColor("#ff9999")
            self._hover_text = QColor("#FFFFFF")
            self._pressed_text = QColor("#ffcccc")

            self._default_border = QColor("#ed4245")
            self._hover_border = QColor("#c53b3e")
            self._pressed_border = QColor("#a83235")

        else:
            raise ValueError("btn_style должен быть 'default', 'positive' или 'negative'")

        # Обновляем текущие значения
        self._bg_color = self._default_bg
        self._text_color = self._default_text
        self._border_color = self._default_border

