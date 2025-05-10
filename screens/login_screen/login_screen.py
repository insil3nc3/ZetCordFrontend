import os
from PyQt6.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QLineEdit, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase, QCursor

from screens.StyleSheets.widgets import line_edit_style, button_style


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ========== Init ==========
        self.setFixedSize()
        self.setFixedSize(800, 500)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        # ==========================

        # ====== stylization ======
        self.setStyleSheet("""
            background-color: #121212;
            color: #E8E8E8;
            font-family: 'Inter', sans-serif;
        """)
        # =========================

        # ====== загрузка шрифта ======
        cur_dir = os.path.dirname(os.path.curdir)
        font_path = os.path.join(cur_dir, "..", "font", "static", "Inter_18pt-Regular.ttf")
        # font_path = "/font/static/Inter_18pt-Regular.ttf"
        font_id = QFontDatabase.addApplicationFont(font_path)  # Загружаем шрифт
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]  # Получаем название шрифта
            self.setFont(QFont(font_family, 12))  # Устанавливаем шрифт по умолчанию
        else:
            print("Ошибка загрузки шрифта.")
        # ==========================

        # ========== Label ==========
        label = QLabel("Войдите в ваш аккаунт ZetCord")
        label.setFont(QFont('Inter', 24, QFont.Weight.ExtraBold))
        main_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignHCenter)
        # ===========================

        # ========== alert ==========
        self.alert = QLabel()
        self.alert.setStyleSheet("color: #FF6347;")
        self.alert.setFont(QFont('Inter', 12, QFont.Weight.Bold))
        main_layout.addWidget(self.alert, alignment=Qt.AlignmentFlag.AlignHCenter)
        # ===========================

        # ========== Email Input ==========
        self.email = QLineEdit()
        self.email.setPlaceholderText("Ваш email")
        self.email.setStyleSheet(line_edit_style)
        self.email.setFixedWidth(300)
        self.email.setFont(QFont('Inter', 12, QFont.Weight.Bold))
        main_layout.addWidget(self.email, alignment=Qt.AlignmentFlag.AlignCenter)
        # =================================

        # ========== Email Input ==========
        self.password = QLineEdit()
        self.email.setPlaceholderText("Ваш пароль")
        self.password.setStyleSheet(line_edit_style)
        self.password.setFixedWidth(300)
        self.password.setFont(QFont('Inter', 12, QFont.Weight.Bold))
        main_layout.addWidget(self.password, alignment=Qt.AlignmentFlag.AlignCenter)
        # =================================

        # ========== Login Button ==========
        login_button = QPushButton("Войти")
        login_button.setStyleSheet(button_style)
        login_button.setFont(QFont('Inter', 18, QFont.Weight.ExtraBold))
        login_button.setFixedWidth(200)
        login_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        # ==================================

