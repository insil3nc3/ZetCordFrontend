from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QListWidget, QHBoxLayout
import os
from PyQt6.QtWidgets import QWidget, QMainWindow
from PyQt6.QtCore import QTimer, pyqtSlot, Qt
from PyQt6.QtGui import QFont, QFontDatabase

from screens.utils.screen_style_sheet import screen_style, load_custom_font


class MainWindow(QMainWindow):
    def __init__(self, user_start_data):
        super().__init__()
        # ========== Init ==========
        self.user_start_data = user_start_data
        self.showMaximized()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        # ==========================

        # ========== Stylization ==========
        self.setStyleSheet(screen_style)
        # =================================

        # ========== Font ==========
        font = load_custom_font(12)
        if font:
            self.setFont(font)
        # =========================

        # ========== User List ==========
        # ====== Private chat List ======
        self.chat_layout = QHBoxLayout()
        self.users_list = QListWidget()
        self.chat_layout.addWidget(self.users_list, alignment=Qt.AlignmentFlag.AlignLeft)
        # ==============================

        # =====  Private chat Items =====
        
        # ===============================
        # ===============================
