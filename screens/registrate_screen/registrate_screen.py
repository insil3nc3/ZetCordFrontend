from PyQt6.QtWidgets import QWidget, QMainWindow, QLineEdit, QPushButton, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtGui import QCursor
from StyleSheets.widgets import line_edit_style, button_style, line_edit_style_alert
from backend.validate.validate_email import validate_email_address
from backend.validate.validate_password import validate_passwords
from PyQt6.QtWidgets import QStackedWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect


class RegistrateWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ========== init ==========
        self.setFixedSize(800, 500)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.view_stack = []  # Хранит историю индексов

        self.profile_create_widget = QWidget()
        self.register_widget = QWidget()
        self.confirm_widget = QWidget()

        self.stack.addWidget(self.register_widget)
        self.stack.addWidget(self.confirm_widget)
        self.stack.addWidget(self.profile_create_widget)

        self.init_register_ui()
        self.init_confirm_ui()
        self.init_profile_create_ui()
        self.anim_in = None
        self.anim_out = None

        # ==========================

        # ====== stylization ======
        self.setStyleSheet("""
            background-color: #121212;
            color: #E8E8E8;
            font-family: 'Inter', sans-serif;
        """)
        # =========================

        # ====== загрузка шрифта ======
        font_path = "/home/zamkid/gitProjects/ZetCordFrontend/font/static/Inter_18pt-Regular.ttf"
        font_id = QFontDatabase.addApplicationFont(font_path)  # Загружаем шрифт
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]  # Получаем название шрифта
            self.setFont(QFont(font_family, 12))  # Устанавливаем шрифт по умолчанию
        else:
            print("Ошибка загрузки шрифта.")
        # ==========================


        self.passwords_valid = None

    def init_register_ui(self):
        main_layout = QVBoxLayout()
        self.register_widget.setLayout(main_layout)
        # ========== widgets ==========
        main_layout.addStretch()
        # ===== Label =====
        label = QLabel("Welcome to Zetcord!")
        label.setFont(QFont('Inter', 24, QFont.Weight.ExtraBold))  # Применяем шрифт для конкретного виджета
        main_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignHCenter)
        # =================

        main_layout.addStretch()

        # ===== Alert Label =====
        self.alert = QLabel("")
        self.alert.setStyleSheet("color: #FF6347;")
        self.alert.setFont(QFont('Inter', 12, QFont.Weight.Bold))
        main_layout.addWidget(self.alert, alignment=Qt.AlignmentFlag.AlignHCenter)
        # =======================
        # ===== Email ====
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        self.email.setStyleSheet(line_edit_style)
        self.email.setFixedWidth(300)
        self.email.setFont(QFont('Inter', 12, QFont.Weight.Bold))
        main_layout.addWidget(self.email, alignment=Qt.AlignmentFlag.AlignCenter)
        # ================

        # ===== Password ====
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setStyleSheet(line_edit_style)
        self.password.setFixedWidth(300)
        self.password.setFont(QFont('Inter', 12, QFont.Weight.Bold))
        main_layout.addWidget(self.password, alignment=Qt.AlignmentFlag.AlignCenter)
        # ================

        # ===== Confirm password ====
        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Confirm password")
        self.confirm_password.setStyleSheet(line_edit_style)
        self.confirm_password.setFixedWidth(300)
        self.confirm_password.setFont(QFont('Inter', 16, QFont.Weight.Bold))
        main_layout.addWidget(self.confirm_password, alignment=Qt.AlignmentFlag.AlignCenter)
        # ================
        main_layout.addStretch()
        # ===== OK button =====
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet(button_style)
        ok_button.setFont(QFont('Inter', 18, QFont.Weight.ExtraBold))
        ok_button.setFixedWidth(200)
        ok_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        ok_button.clicked.connect(self.send_data)
        main_layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)
        # =====================

        main_layout.addStretch()

        # =============================

    def init_confirm_ui(self):
        main_layout = QVBoxLayout()
        self.confirm_widget.setLayout(main_layout)
        #====================

        back_button = QPushButton("Назад")
        back_button.setStyleSheet(button_style)
        back_button.setFont(QFont('Inter', 18, QFont.Weight.ExtraBold))
        back_button.setFixedWidth(200)
        back_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_button.clicked.connect(self.go_back)
        main_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def init_profile_create_ui(self):
        layout = QVBoxLayout()
        self.profile_create_widget.setLayout(layout)

        label = QLabel("Третий экран")
        label.setFont(QFont('Inter', 20, QFont.Weight.ExtraBold))
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

        back_btn = QPushButton("Назад")
        back_btn.setStyleSheet(button_style)
        back_btn.clicked.connect(self.go_back)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def go_back(self):
        if self.view_stack:
            previous_index = self.view_stack.pop()
            self.animate_transition(previous_index, is_back=True)


    def send_data(self):
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

        self.alert.setStyleSheet("color: #00FF00;")
        self.alert.setText("Успешно!")
        self.animate_transition(to_index=1)

    def password_alert(self, success=False):
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

    def email_alert(self, success=False):
        self.alert.setStyleSheet("color: #FF6347;")
        if self.email.text() == "":
            self.alert.setText("Почта не может быть пустой")
        else:
            self.alert.setText("Введите корректную почту")
        self.email.setStyleSheet(line_edit_style_alert)
        QTimer.singleShot(2000, lambda: self.alert.setText(""))
        QTimer.singleShot(2000, lambda: self.email.setStyleSheet(line_edit_style))

    def animate_transition(self, to_index: int, is_back=False):
        current_index = self.stack.currentIndex()
        if current_index == to_index:
            return

        current_widget = self.stack.widget(current_index)
        next_widget = self.stack.widget(to_index)
        geo = self.stack.geometry()
        offset = geo.width()

        direction = 1 if is_back else -1

        next_widget.setGeometry(QRect(offset * direction, 0, geo.width(), geo.height()))
        next_widget.show()

        self.anim_out = QPropertyAnimation(current_widget, b"pos", self)
        self.anim_out.setDuration(1000)
        self.anim_out.setStartValue(current_widget.pos())
        self.anim_out.setEndValue(current_widget.pos() + QPoint(offset * direction, 0))
        self.anim_out.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.anim_in = QPropertyAnimation(next_widget, b"pos", self)
        self.anim_in.setDuration(1000)
        self.anim_in.setStartValue(QPoint(-offset * direction, 0))
        self.anim_in.setEndValue(QPoint(0, 0))
        self.anim_in.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def on_animation_finished():
            self.stack.setCurrentIndex(to_index)
            current_widget.move(0, 0)
            next_widget.setGeometry(geo)
            if not is_back:
                self.view_stack.append(current_index)  # Добавляем текущий в историю

        self.anim_in.finished.connect(on_animation_finished)
        self.anim_out.start()
        self.anim_in.start()




