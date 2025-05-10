import asyncio

from PyQt6.QtWidgets import QWidget, QMainWindow, QLineEdit, QPushButton, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtGui import QCursor

from screens.utils.animate_button import StyledAnimatedButton


def init_register_ui(
    register_widget,
    send_data_callback,
    line_edit_style: str,
    button_style: str
):
    main_layout = QVBoxLayout()
    register_widget.setLayout(main_layout)

    main_layout.addStretch()

    label = QLabel("Welcome to Zetcord!")
    label.setFont(QFont('Inter', 24, QFont.Weight.ExtraBold))
    main_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignHCenter)

    main_layout.addStretch()

    alert = QLabel("")
    alert.setStyleSheet("color: #FF6347;")
    alert.setFont(QFont('Inter', 12, QFont.Weight.Bold))
    main_layout.addWidget(alert, alignment=Qt.AlignmentFlag.AlignHCenter)

    email = QLineEdit()
    email.setPlaceholderText("Email")
    email.setStyleSheet(line_edit_style)
    email.setFixedWidth(300)
    email.setFont(QFont('Inter', 12, QFont.Weight.Bold))
    main_layout.addWidget(email, alignment=Qt.AlignmentFlag.AlignCenter)

    password = QLineEdit()
    password.setPlaceholderText("Password")
    password.setStyleSheet(line_edit_style)
    password.setFixedWidth(300)
    password.setFont(QFont('Inter', 16, QFont.Weight.Bold))
    main_layout.addWidget(password, alignment=Qt.AlignmentFlag.AlignCenter)

    confirm_password = QLineEdit()
    confirm_password.setPlaceholderText("Confirm password")
    confirm_password.setStyleSheet(line_edit_style)
    confirm_password.setFixedWidth(300)
    confirm_password.setFont(QFont('Inter', 16, QFont.Weight.Bold))
    main_layout.addWidget(confirm_password, alignment=Qt.AlignmentFlag.AlignCenter)


    main_layout.addStretch()

    ok_button = StyledAnimatedButton("OK")
    ok_button.clicked.connect(lambda: asyncio.create_task(send_data_callback()))
    main_layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)

    main_layout.addStretch()

    return email, password, confirm_password, alert