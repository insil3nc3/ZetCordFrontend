import asyncio

from PyQt6.QtWidgets import QWidget, QMainWindow, QLineEdit, QPushButton, QLabel, QVBoxLayout, QApplication, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPoint, QRegularExpression
from PyQt6.QtGui import QFont, QFontDatabase, QRegularExpressionValidator, QCursor

from screens.utils.animate_button import StyledAnimatedButton


def init_confirm_ui(confirm_widget, go_back_callback, code_confirm_style_sheet, button_style, confirm_reg_callback):
    main_layout = QVBoxLayout()
    confirm_widget.setLayout(main_layout)
    # ====================
    main_layout.addStretch()
    # ===== Label =====
    label = QLabel("Код подтверждения был \nотправлен на вашу почту")
    label.setFont(QFont('Inter', 18, QFont.Weight.ExtraBold))
    main_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
    # =================


    # ===== Confirm alert =====
    confirm_alert = QLabel("")
    confirm_alert.setFont(QFont('Inter', 18, QFont.Weight.Bold))
    main_layout.addWidget(confirm_alert, alignment=Qt.AlignmentFlag.AlignCenter)
    # =========================

    # ===== Code EditLine =====
    confirm_code = QLineEdit()
    confirm_code.setStyleSheet(code_confirm_style_sheet)
    confirm_code.setMaxLength(6)  # Максимум 6 символов
    confirm_code.setFixedSize(260, 75)  # Размер поля
    confirm_code.setFont(QFont("Inter", 32, QFont.Weight.ExtraBold))
    confirm_code.setAlignment(Qt.AlignmentFlag.AlignCenter)

    main_layout.addWidget(confirm_code, alignment=Qt.AlignmentFlag.AlignCenter)
    # =========================

    # ===== Confirm button =====
    main_layout.addStretch()
    button_layout = QHBoxLayout()
    confirm_button = StyledAnimatedButton("Подтвердить")
    confirm_button.clicked.connect(lambda: asyncio.create_task(confirm_reg_callback()))

    # ==========================

    # ===== Back button =====
    back_button = StyledAnimatedButton("Назад")
    back_button.clicked.connect(go_back_callback)

    # ========================
    button_layout.addStretch()
    button_layout.addWidget(back_button)
    button_layout.addWidget(confirm_button)
    main_layout.addLayout(button_layout)
    button_layout.addStretch()
    main_layout.addStretch()

    return confirm_alert, confirm_code