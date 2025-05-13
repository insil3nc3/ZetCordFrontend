from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel

from screens.utils.screen_style_sheet import load_custom_font


class MessageWidget(QWidget):
    def __init__(self, data: dict, sender):
        super().__init__()
        self.msg_text = data["content"]
        self.msg_sender = sender
        self.msg_time = data["timestamp"]
        self.msg_read = data["read"]
        self.msg_edited = data["edited"]

        # ====== загрузка шрифта ======
        font = load_custom_font(12)
        if font:
            self.setFont(font)
        # ==========================

        # ========== Initialization ==========
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        self.msg_container = QWidget()
        msg_layout = QHBoxLayout()
        msg_layout.setContentsMargins(10, 6, 10, 6)
        msg_layout.setSpacing(5)
        if self.msg_sender == "user":
            msg_color = "#312b33"
        else:
            msg_color = "#141015"
        self.msg_container.setStyleSheet(f"""
            background-color: {msg_color};
            border-radius: 12px;
        """)
        # ====================================

        # ========== Msg text ==========
        self.text = QLabel(self.msg_text)
        self.text.setFont(QFont("Inter", 12, QFont.Weight.Normal))
        self.text.setStyleSheet("color: #FFFFFF;")
        msg_layout.addWidget(self.text)

        # ==============================

        # ========== Msg time ==========
        dt = datetime.fromisoformat(self.msg_time)
        time_wrapper = QWidget()
        time_layout = QVBoxLayout()
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.addStretch()
        self.time = QLabel(dt.strftime("%H:%M"))
        self.time.setFont(QFont("Inter", 8, QFont.Weight.Normal))
        self.time.setStyleSheet("color: gray;")
        time_layout.addWidget(self.time, alignment=Qt.AlignmentFlag.AlignRight)
        time_wrapper.setLayout(time_layout)
        msg_layout.addWidget(time_wrapper, alignment=Qt.AlignmentFlag.AlignBottom)
        # ==============================

        # ========== Msg edited ==========
        self.edited = QLabel()
        self.edited.setFont(QFont("Inter", 10, QFont.Weight.Normal))
        self.edited.setStyleSheet("color: gray;")
        self.edited.setText("")
        # ==============================
        self.msg_container.setLayout(msg_layout)
        main_layout.addWidget(self.msg_container)
        main_layout.addStretch()

    def change_status(self, obj: str, data=None):
        if obj == "read":
            self.msg_container.setStyleSheet(f"""
            background-color: "#322536";
            border-radius: 12px;
        """)
        elif obj == "edited":
            self.text.setText(data)
            self.edited.setText("изменено")
