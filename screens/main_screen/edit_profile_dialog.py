import asyncio
import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QCursor
from PyQt6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QFileDialog, QWidget
)

from api.profile_actions import edit_nickname, edit_unique_name, upload_avatar
from screens.utils.animate_button import StyledAnimatedButton
from screens.utils.circular_photo import create_circular_pixmap
from screens.utils.default_avatar import default_ava_path
from screens.utils.screen_style_sheet import load_custom_font, screen_style
from screens.utils.widgets import main_screen_line_edit_style


class EditProfileDialog(QDialog):
    def __init__(self, initial_nickname="", initial_unique_name="", avatar_path=None, send_via_ws_callback=None,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Изменение профиля")
        self.setModal(True)
        self.setFixedSize(550, 300)
        self.initial_nickname = initial_nickname
        self.initial_unique_name = initial_unique_name
        self.initial_avatar_path = avatar_path
        self.send_via_ws_callback = send_via_ws_callback

        self.setStyleSheet(screen_style)

        font = load_custom_font(12)
        if font:
            self.setFont(font)

        self.avatar_path = avatar_path

        main_layout = QVBoxLayout(self)

        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(20)

        # Аватарка слева
        self.avatar = QLabel()
        self.avatar.setFixedSize(120, 120)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.avatar.mousePressEvent = self.select_avatar
        self.set_avatar(self.avatar_path)

        # Текстовые поля справа
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(10)

        self.nickname_input = QLineEdit()
        self.nickname_input.setPlaceholderText("Никнейм")
        self.nickname_input.setFont(QFont("inter", 16, QFont.Weight.Bold))
        self.nickname_input.setMinimumHeight(50)
        self.nickname_input.setStyleSheet(main_screen_line_edit_style)
        self.nickname_input.setText(initial_nickname)
        form_layout.addWidget(self.nickname_input)

        self.unique_name_input = QLineEdit()
        self.unique_name_input.setPlaceholderText("@уникальное_имя")
        self.unique_name_input.setFont(QFont("inter", 16, QFont.Weight.Bold))
        self.unique_name_input.setMinimumHeight(50)
        self.unique_name_input.setStyleSheet(main_screen_line_edit_style)
        self.unique_name_input.setText(initial_unique_name)

        def on_text_changed():
            if not self.unique_name_input.text().startswith("@"):
                self.unique_name_input.setText("@" + self.unique_name_input.text())

        self.unique_name_input.textChanged.connect(on_text_changed)
        form_layout.addWidget(self.unique_name_input)

        top_layout.addWidget(self.avatar)
        top_layout.addWidget(form_widget)

        # Кнопки
        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.confirm_button = StyledAnimatedButton(text="Подтвердить", width=200, btn_style="positive")
        self.cancel_button = StyledAnimatedButton(text="Отмена", width=200, btn_style="negative")
        self.cancel_button.clicked.connect(self.reject)
        self.confirm_button.clicked.connect(lambda x: asyncio.create_task(self.accept_changes()))

        button_layout.addStretch()
        button_layout.addWidget(self.confirm_button, alignment=Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(self.cancel_button, alignment=Qt.AlignmentFlag.AlignCenter)


        # Добавляем в главный layout
        main_layout.addWidget(top_widget)
        main_layout.addStretch()
        main_layout.addWidget(button_row)

    def set_avatar(self, path=None):
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
        elif default_ava_path and os.path.exists(default_ava_path):
            pixmap = QPixmap(default_ava_path)
        else:
            pixmap = QPixmap(120, 120)
            pixmap.fill(Qt.GlobalColor.lightGray)

        circular = create_circular_pixmap(pixmap, 120)
        self.avatar.setPixmap(circular)
        self.avatar.setScaledContents(True)

    async def accept_changes(self):
        self.accept()
        if self.nickname_input.text().strip() != self.initial_nickname:
            await edit_nickname(self.nickname_input.text().strip())
        if self.unique_name_input.text().strip() != self.initial_unique_name:
            await edit_unique_name(self.unique_name_input.text().strip())
        if self.avatar_path != self.initial_avatar_path:
            await upload_avatar(self.avatar_path)
        self.send_via_ws_callback({"type": "init"})

    def select_avatar(self, event):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.webp)")
        if file_dialog.exec():
            selected = file_dialog.selectedFiles()
            if selected:
                self.avatar_path = selected[0]
                self.set_avatar(self.avatar_path)

    def get_data(self):
        return {
            "nickname": self.nickname_input.text().strip(),
            "unique_name": self.unique_name_input.text().strip(),
            "avatar_path": self.avatar_path
        }