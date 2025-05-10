from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from screens.utils.default_avatar import default_ava_path
from screens.utils.circular_photo import create_circular_pixmap


class DialogItem(QWidget):
    def __init__(self, username, last_msg=None, avatar_path=None, chat_id=None, user_id=None):
        super().__init__()
        self.full_username = username if username else "Unknown"
        self.last_msg_text = last_msg if last_msg else "Нет сообщений"
        self.compact_mode = False

        # ========== Layout setup ==========
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setStyleSheet("background: transparent;")
        # ==============================

        # ========== Avatar label ==========
        self.avatar = QLabel()
        selected_path = avatar_path if avatar_path else default_ava_path
        pixmap = QPixmap(selected_path)
        circular_pixmap = create_circular_pixmap(pixmap, 40)
        self.avatar.setPixmap(circular_pixmap)
        self.avatar.setStyleSheet("background: transparent;")
        self.layout.addWidget(self.avatar)
        # ==============================

        # ========== Label layout ==========
        self.label_layout = QVBoxLayout()
        # ==============================

        # ========== Name label ==========
        self.name_label = QLabel(self.full_username)
        self.name_label.setStyleSheet("color: white; font-weight: bold; background: transparent;")
        self.label_layout.addWidget(self.name_label)
        # ==============================

        # ========== Last message label ==========
        self.last_msg_label = QLabel(self.last_msg_text)
        self.last_msg_label.setStyleSheet("color: gray; background: transparent;")
        self.label_layout.addWidget(self.last_msg_label)
        # ==============================

        self.layout.addLayout(self.label_layout)
        self.layout.addStretch()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

        # ========== Instance attributes ==========
        self.username = username
        self.chat_id = chat_id
        self.user_id = user_id
        # ==============================

    def set_compact_mode(self, compact):
        # ========== Переключение режима отображения ==========
        self.compact_mode = compact
        if compact:
            # Сокращенный режим: только 4 символа имени и без last_msg
            short_name = self.full_username[:4] + "..." if len(self.full_username) > 4 else self.full_username
            self.name_label.setText(short_name)
            self.last_msg_label.setVisible(False)
        else:
            # Полный режим: полное имя и last_msg
            self.name_label.setText(self.full_username)
            self.last_msg_label.setVisible(True)
        # ==============================


    def set_selected_style(self):
        self.setStyleSheet("""
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 #9B4DCA, stop: 1 #6D39A8
            );
            border-radius: 8px;
        """)

    def set_default_style(self):
        self.setStyleSheet("""
            background: transparent;
        """)