import asyncio
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QPainter, QPainterPath, QLinearGradient, QColor
from PyQt6.QtWidgets import QWidget, QLabel

from api.profile_actions import get_current_user, download_avatar
from screens.utils.circular_photo import create_circular_pixmap
from screens.utils.default_avatar import default_ava_path


class MyProfile(QWidget):
    def __init__(self):
        super().__init__()


        self.setFixedHeight(90)
        self.setFixedWidth(300)

        # Устанавливаем градиентный фон через стиль
        self.setStyleSheet("""
            MyProfile {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6C4AB6, stop:1 #5D3FD3
                );
                border-radius: 10px;
            }
        """)

        # Аватар
        self.avatar = QLabel(self)
        self.avatar.setFixedSize(70, 70)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet("background: transparent;")
        self.avatar.setGeometry(10, 10, 70, 70)  # Позиция: x=10, y=10

        # Имя пользователя
        self.username = QLabel("Username", self)
        self.username.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.username.setStyleSheet("background: transparent; color: white;")
        font = QFont()
        font.setPointSize(12)
        self.username.setFont(font)
        self.username.setGeometry(90, 20, 200, 20)  # Позиция: x=90, y=20

        # Уникальное имя
        self.unique_name = QLabel("unique_name", self)
        self.unique_name.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.unique_name.setStyleSheet("background: transparent; color: white;")
        font = QFont()
        font.setPointSize(10)
        self.unique_name.setFont(font)
        self.unique_name.setGeometry(90, 45, 200, 20)  # Позиция: x=90, y=45



    def paintEvent(self, event):
        """Рисуем градиентный фон вручную для надежности."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Создаем градиент
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#6C4AB6"))
        gradient.setColorAt(1, QColor("#5D3FD3"))

        # Рисуем прямоугольник с закругленными углами
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        painter.fillPath(path, gradient)
        painter.end()



    async def input_data(self, data):
        full_data = data
        profile_data = full_data.get("profile_data", {})

        avatar_path = await download_avatar(profile_data.get("id"))
        pixmap = QPixmap(avatar_path if avatar_path else default_ava_path)

        # Преобразуем изображение в круглое
        circular_pixmap = create_circular_pixmap(pixmap, 70)
        self.avatar.setPixmap(circular_pixmap)

        self.username.setText(profile_data.get("nickname", "Имя"))
        self.unique_name.setText(profile_data.get("unique_name", "user"))

