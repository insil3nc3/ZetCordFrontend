import asyncio
import os
from PyQt6.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QLineEdit, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QFont, QFontDatabase, QCursor

from api.auth import login
from backend.check_for_token import check_for_token_existing
from backend.validate.validate_email import validate_email_address
from backend.validate.validate_password import validate_passwords
from screens.utils.animate_button import StyledAnimatedButton
from screens.utils.animate_text_button import AnimatedButton
from screens.utils.screen_style_sheet import screen_style, load_custom_font
from screens.utils.widgets import line_edit_style, button_style, line_edit_style_alert

import time

from screens.main_screen.main_screen import MainWindow
from screens.registrate_screen.registrate_screen import RegistrateWindow


class LoginWindow(QMainWindow):
    def __init__(self, alert=None, user_start_data=None):
        super().__init__()
        # ========== Init ==========
        self.main_window = None
        self.setFixedSize(800, 500)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.user_start_data = user_start_data
        # ==========================

        # ====== stylization ======
        self.setStyleSheet(screen_style)
        # =========================

        # ========== Font ==========
        font = load_custom_font(12)
        if font:
            self.setFont(font)
        # =========================

        main_layout.addStretch()
        # ========== Label ==========
        label = QLabel("ZetCord")
        label.setFont(QFont('Inter', 28, QFont.Weight.ExtraBold))
        main_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignHCenter)
        # ===========================

        # ========== alert ==========
        self.alert = QLabel(alert)
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

        # ========== password Input ==========
        self.password = QLineEdit()
        self.password.setPlaceholderText("Ваш пароль")
        self.password.setStyleSheet(line_edit_style)
        self.password.setFixedWidth(300)
        self.password.setFont(QFont('Inter', 12, QFont.Weight.Bold))
        main_layout.addWidget(self.password, alignment=Qt.AlignmentFlag.AlignCenter)
        # =================================

        # ========== Login Button ==========
        login_button = StyledAnimatedButton("Войти")
        login_button.clicked.connect(lambda: asyncio.create_task(self.login()))
        main_layout.addWidget(login_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # ==================================

        main_layout.addStretch()

        # ============ Register button ============
        register_button = AnimatedButton("Зарегистрироваться")
        register_button.clicked.connect(self.go_to_registration)
        main_layout.addWidget(register_button, alignment=Qt.AlignmentFlag.AlignCenter)
        # =====================================
        main_layout.addStretch()


    @pyqtSlot()
    async def login(self):
        email = self.email.text()
        password = self.password.text()
        email_valid = validate_email_address(email)
        if not email_valid:
            self.email_alert()
            return None
        token_exist = check_for_token_existing()
        result = await login(email, password)
        if "request error" in result:
            self.alert.setStyleSheet("color: #FF6347;")
            self.alert.setText(result["request error"])
            return
        self.alert.setStyleSheet("color: #00FF00;")
        self.alert.setText("Успешно!")
        self.close()
        self.main_window = MainWindow()
        self.main_window.show()

    def email_alert(self):
        self.alert.setStyleSheet("color: #FF6347;")
        if self.email.text() == "":
            self.alert.setText("Почта не может быть пустой")
        else:
            self.alert.setText("Введите корректную почту")
        self.email.setStyleSheet(line_edit_style_alert)
        QTimer.singleShot(2000, lambda: self.alert.setText(""))
        QTimer.singleShot(2000, lambda: self.email.setStyleSheet(line_edit_style))

    def go_to_registration(self):
        self.close()
        register_window = RegistrateWindow()
        register_window.show()