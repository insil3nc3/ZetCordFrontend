import asyncio
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPixmap, QFont, QPainter, QPainterPath, QLinearGradient, QColor
from PyQt6.QtWidgets import QWidget, QLabel

from api.profile_actions import get_current_user, download_avatar
from screens.utils.circular_photo import create_circular_pixmap
from screens.utils.default_avatar import default_ava_path
from screens.utils.screen_style_sheet import load_custom_font


class MyProfile(QWidget):
    def __init__(self):
        super().__init__()
        self.avatar_path = None

        self.setFixedHeight(90)
        self.setFixedWidth(300)

        # ====== загрузка шрифта ======
        font = load_custom_font(12)
        if font:
            self.setFont(font)
        # ==========================

        # Устанавливаем градиентный фон через стиль

        # Аватар
        self.avatar = QLabel(self)
        self.avatar.setFixedSize(70, 70)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet("background: transparent;")
        self.avatar.setGeometry(10, 10, 70, 70)  # Позиция: x=10, y=10

        # Имя пользователя
        self.username = QLabel("Username", self)
        self.username.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        self.username.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.username.setStyleSheet("background: transparent; color: white;")
        self.username.setGeometry(90, 20, 200, 20)  # Позиция: x=90, y=20

        # Уникальное имя
        self.unique_name = QLabel("unique_name", self)
        self.unique_name.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.unique_name.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.unique_name.setStyleSheet("background: transparent; color: gray;")
        self.unique_name.setGeometry(90, 50, 200, 20)  # Позиция: x=90, y=45

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        outer_rect = QRectF(self.rect())  # Преобразование к QRectF
        border_radius = 10
        border_thickness = 3

        # Градиент для рамки
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#4C2A57"))
        gradient.setColorAt(1, QColor("#7A4165"))

        outer_path = QPainterPath()
        outer_path.addRoundedRect(outer_rect, border_radius, border_radius)

        inner_rect = outer_rect.adjusted(
            border_thickness, border_thickness,
            -border_thickness, -border_thickness
        )
        inner_path = QPainterPath()
        inner_path.addRoundedRect(inner_rect, border_radius - 1, border_radius - 1)

        border_path = outer_path.subtracted(inner_path)
        painter.fillPath(border_path, gradient)
        painter.fillPath(inner_path, QColor("#121212"))

        painter.end()



    async def input_data(self, data):
        full_data = data
        profile_data = full_data.get("profile_data", {})

        self.avatar_path = await download_avatar(profile_data.get("id"))
        pixmap = QPixmap(self.avatar_path if self.avatar_path else default_ava_path)

        # Преобразуем изображение в круглое
        circular_pixmap = create_circular_pixmap(pixmap, 70)
        self.avatar.setPixmap(circular_pixmap)

        self.username.setText(profile_data.get("nickname", "Имя"))
        self.unique_name.setText(profile_data.get("unique_name", "user"))

