import asyncio

from PyQt6.QtWidgets import QWidget, QMainWindow, QLineEdit, QPushButton, QLabel, QVBoxLayout, QApplication, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtGui import QCursor

from screens.utils.animate_button import StyledAnimatedButton


def init_profile_create_ui(profile_create_widget, go_back_callback, line_edit_style, button_style, go_next_callback):
    main_layout = QVBoxLayout()
    profile_create_widget.setLayout(main_layout)

    main_layout.addStretch()

    # ===== Label =====

    label = QLabel("Последний шаг!")
    label.setFont(QFont('Inter', 20, QFont.Weight.ExtraBold))
    main_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
    # =================

    # ===== Label =====
    label = QLabel("Придумайте свои данные")
    label.setFont(QFont('Inter', 16, QFont.Weight.Bold))
    main_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
    # =================
    main_layout.addStretch()
    # ===== Nickname =====
    nickname = QLineEdit()
    nickname.setPlaceholderText("никнейм")
    nickname.setStyleSheet(line_edit_style)
    nickname.setFont(QFont('Inter', 20, QFont.Weight.Bold))
    nickname.setFixedWidth(300)
    main_layout.addWidget(nickname, alignment=Qt.AlignmentFlag.AlignCenter)
    # ====================

    # ===== Unique name =====
    def on_text_changed():
        # Если строка не начинается с "@", добавляем его
        if not unique_name.text().startswith('@'):
            unique_name.setText('@' + unique_name.text()[0:])

    unique_name = QLineEdit()
    unique_name.setPlaceholderText("@Уникальное имя")
    unique_name.setStyleSheet(line_edit_style)
    unique_name.setFont(QFont('Inter', 19, QFont.Weight.Bold))
    unique_name.setFixedWidth(300)
    unique_name.textChanged.connect(on_text_changed)
    main_layout.addWidget(unique_name, alignment=Qt.AlignmentFlag.AlignCenter)
    # ====================

    # ====== Ok button ======
    main_layout.addStretch()
    ok_button = StyledAnimatedButton("Ок")
    ok_button.clicked.connect(lambda: asyncio.create_task(go_next_callback()))
    ok_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    # =========================

    # ====== Back button ======
    main_layout.addStretch()
    back_btn = StyledAnimatedButton("Назад")
    back_btn.clicked.connect(go_back_callback)
    back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    # =========================
    button_layout = QHBoxLayout()
    button_layout.addStretch()
    button_layout.addWidget(back_btn)
    button_layout.addWidget(ok_button)
    button_layout.addStretch()
    main_layout.addLayout(button_layout)
    main_layout.addStretch()

    return unique_name, nickname, label