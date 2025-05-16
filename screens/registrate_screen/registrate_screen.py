import os
from sys import exception

from PyQt6.QtWidgets import QWidget, QMainWindow
from PyQt6.QtCore import QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QFontDatabase
from jaraco.functools import except_

from screens.utils.screen_style_sheet import screen_style, load_custom_font
from screens.utils.widgets import line_edit_style, button_style, line_edit_style_alert, code_confirm_style_sheet, nickname_style_sheet
from backend.validate.validate_email import validate_email_address
from backend.validate.validate_password import validate_passwords
from PyQt6.QtWidgets import QStackedWidget

from screens.registrate_screen.init_register import init_register_ui
from screens.registrate_screen.init_confirm import init_confirm_ui
from screens.registrate_screen.init_profile_create import init_profile_create_ui
from screens.registrate_screen.transition import animate_transition
from screens.main_screen.main_screen import MainWindow

from api.auth import request_code, register
from api.profile_actions import edit_nickname, edit_unique_name, get_current_user


class RegistrateWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ========== init ==========
        self.setFixedSize(800, 500)
        self.main_window = None
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.view_stack = []  # Хранит историю индексов

        self.profile_create_widget = QWidget()
        self.register_widget = QWidget()
        self.confirm_widget = QWidget()

        self.stack.addWidget(self.register_widget)
        self.stack.addWidget(self.confirm_widget)
        self.stack.addWidget(self.profile_create_widget)

        self.email, self.password, self.confirm_password, self.alert = init_register_ui(register_widget=self.register_widget, send_data_callback=self.send_data, line_edit_style=line_edit_style, button_style=button_style)
        self.confirm_alert, self.confirm_code = init_confirm_ui(confirm_widget=self.confirm_widget, go_back_callback=self.go_back, code_confirm_style_sheet=code_confirm_style_sheet, button_style=button_style, confirm_reg_callback=self.confirm_reg)
        self.unique_name, self.nickname, self.label = init_profile_create_ui(profile_create_widget=self.profile_create_widget, go_back_callback=self.go_back, line_edit_style=nickname_style_sheet, button_style=button_style, go_next_callback=self.open_main_menu)
        self.anim_in = None
        self.anim_out = None

        # ==========================

        # ====== stylization ======
        self.setStyleSheet(screen_style)
        # =========================

        # ====== загрузка шрифта ======
        font = load_custom_font(12)
        if font:
            self.setFont(font)
        # ==========================


        self.passwords_valid = None

    def go_back(self):
        if self.view_stack:
            previous_index = self.view_stack.pop()
            animate_transition(self, previous_index, is_back=True)

    @pyqtSlot()
    async def confirm_reg(self):
        code = self.confirm_code.text()
        result = await register(self.email.text(), self.password.text(), code)
        if "request error" in result:
            self.confirm_alert.setStyleSheet("color: #FF6347;")
            self.confirm_alert.setFont(QFont("Inter", 14, QFont.Weight.Bold))
            self.confirm_alert.setText(result["request error"])
            return
        self.confirm_alert.setStyleSheet("color: #00FF00;")
        self.confirm_alert.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        self.confirm_alert.setText("Успешно!")
        animate_transition(self, to_index=2)

    @pyqtSlot()
    async def to_profile(self):
        animate_transition(self, to_index=1)

    def to_open(self):
        self.close()
        try:
            self.main_window = MainWindow()
            self.main_window.showFullScreen()
        except exception as e:
            print(e)


    @pyqtSlot()
    async def open_main_menu(self):
        name = self.nickname.text()
        unique_name = self.unique_name.text()

        # Сохраняем никнейм
        result = await edit_nickname(name)
        if "request error" in result:
            self.label.setStyleSheet("color: #FF6347;")
            self.label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
            self.label.setText(result["request error"])
            return

        # Сохраняем уникальное имя
        result = await edit_unique_name(unique_name)
        if "request error" in result:
            self.label.setStyleSheet("color: #FF6347;")
            self.label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
            self.label.setText(result["request error"])
            return

        # Получаем данные пользователя
        user_start_data = await get_current_user()
        if "request error" in user_start_data:
            self.label.setStyleSheet("color: #FF6347;")
            self.label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
            self.label.setText("Ошибка получения данных, попробуйте снова")
            return

        # Устанавливаем сообщение об успехе
        self.label.setStyleSheet("color: #00FF00;")
        self.label.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        self.label.setText("Успешно!")

        # Создаем и показываем MainWindow
        try:
            self.main_window = MainWindow()
            self.main_window.show()
            self.close()  # Закрываем текущее окно только после отображения MainWindow
        except Exception as e:
            self.label.setStyleSheet("color: #FF6347;")
            self.label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
            self.label.setText(f"Ошибка открытия главного окна: {str(e)}")
            return

    @pyqtSlot()
    async def send_data(self):
        email = self.email.text()
        password = self.password.text()
        confirm_password = self.confirm_password.text()
        email_valid = validate_email_address(email)
        self.passwords_valid = validate_passwords(password, confirm_password)
        if self.passwords_valid !="Успешно!" or not email_valid:
            if self.passwords_valid != "Успешно!":
                self.password_alert()
            if not email_valid:
                self.email_alert()
            return None
        result = await request_code(email)
        if "request error" in result:
            self.alert.setStyleSheet("color: #FF6347;")
            self.alert.setText(result["request error"])
            return
        self.alert.setStyleSheet("color: #00FF00;")
        self.alert.setText("Успешно!")
        animate_transition(self, to_index=1)

    def password_alert(self):
        self.alert.setStyleSheet("color: #FF6347;")
        if self.password.text() == "":
            self.alert.setText("Пароль не может быть пустым")
        else:
            self.alert.setText(self.passwords_valid)
        self.password.setStyleSheet(line_edit_style_alert)
        self.confirm_password.setStyleSheet(line_edit_style_alert)
        QTimer.singleShot(2000, lambda: self.alert.setText(""))
        QTimer.singleShot(2000, lambda: self.password.setStyleSheet(line_edit_style))
        QTimer.singleShot(2000, lambda: self.confirm_password.setStyleSheet(line_edit_style))

    def email_alert(self):
        self.alert.setStyleSheet("color: #FF6347;")
        if self.email.text() == "":
            self.alert.setText("Почта не может быть пустой")
        else:
            self.alert.setText("Введите корректную почту")
        self.email.setStyleSheet(line_edit_style_alert)
        QTimer.singleShot(2000, lambda: self.alert.setText(""))
        QTimer.singleShot(2000, lambda: self.email.setStyleSheet(line_edit_style))
