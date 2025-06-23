import asyncio
from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QPixmap, QFont, QPainter, QPainterPath, QLinearGradient, QColor, QIcon, QCursor
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
from click import clear

from api.profile_actions import download_avatar
from screens.utils.circular_photo import create_circular_pixmap
from screens.utils.default_avatar import default_ava_path
from screens.utils.screen_style_sheet import load_custom_font


class MyProfile(QWidget):
    def __init__(self, exit_callback=None, settings_callback=None):
        super().__init__()
        self.avatar_path = None
        self.exit = exit_callback
        self.settings = settings_callback

        self.setFixedHeight(90)
        self.setFixedWidth(300)

        # ====== загрузка шрифта ======
        font = load_custom_font(12)
        if font:
            self.setFont(font)
        # ==========================

        # === Главный горизонтальный контейнер ===
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        self.setLayout(main_layout)

        # ====== Аватар ======
        self.avatar = QLabel()
        self.avatar.setFixedSize(70, 70)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet("background: transparent;")
        main_layout.addWidget(self.avatar)

        # ====== Информация о пользователе ======
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.username = QLabel("Username")
        self.username.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        self.username.setStyleSheet("background: transparent; color: white;")
        info_layout.addWidget(self.username)

        self.unique_name = QLabel("unique_name")
        self.unique_name.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.unique_name.setStyleSheet("background: transparent; color: gray;")
        info_layout.addWidget(self.unique_name)

        main_layout.addLayout(info_layout)
        main_layout.addStretch()
        # ====== Кнопки (Настройки, Выход) ======
        self.settings_button = QPushButton()
        self.settings_button.setIcon(QIcon("icons/settings.svg"))
        self.settings_button.setIconSize(QSize(32, 32))
        self.settings_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.settings_button.setStyleSheet("border: none;")
        self.settings_button.clicked.connect(lambda: self.settings() if self.settings else None)

        self.exit_button = QPushButton()
        self.exit_button.setIcon(QIcon("icons/exit.svg"))
        self.exit_button.setIconSize(QSize(32, 32))
        self.exit_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.exit_button.setStyleSheet("border: none;")
        self.exit_button.clicked.connect(lambda: self.exit() if self.exit else None)

        button_layout = QVBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addWidget(self.settings_button, alignment=Qt.AlignmentFlag.AlignRight)
        button_layout.addWidget(self.exit_button, alignment=Qt.AlignmentFlag.AlignRight)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        # Правильное выравнивание
        main_layout.addStretch()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        outer_rect = QRectF(self.rect())
        border_radius = 10
        border_thickness = 3

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
        print("input data вызван - ", data)
        self.avatar_path = None
        self.username.clear()
        self.unique_name.clear()
        profile_data = data.get("profile_data", {})
        self.avatar_path = await download_avatar(profile_data.get("id"))
        pixmap = QPixmap(self.avatar_path or default_ava_path)
        circular_pixmap = create_circular_pixmap(pixmap, 70)
        self.avatar.setPixmap(circular_pixmap)
        self.username.setText(profile_data.get("nickname", "Имя"))
        self.unique_name.setText(profile_data.get("unique_name", "user"))

