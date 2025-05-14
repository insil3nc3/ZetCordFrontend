import asyncio

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QWidget, QHBoxLayout

from api.private_chat import create_chat
from api.profile_actions import search_user
from screens.utils.animate_button import StyledAnimatedButton
from screens.utils.screen_style_sheet import screen_style, load_custom_font
from screens.utils.search_screen_profile_widget import SearchScreenProfileWidget
from screens.utils.widgets import line_edit_style, main_screen_line_edit_style
from screens.main_screen.search_screen_switcher import AnimatedSwitcher


class UserSearchWidget(QDialog):
    def __init__(self, open_chat_callback, insert_item_to_list_callback, focus_to_widget_callback, parent=None, cur_user=None):
        super().__init__(parent)
        self.cur_user = cur_user
        self.pos_btn = {"text": "Открыть чат", "connect": "open_chat"}
        self.un_name = None
        self.user_widget = None
        self.user_data = None
        self.open_chat = open_chat_callback
        self.focus_to_widget = focus_to_widget_callback
        self.insert_to_list = insert_item_to_list_callback
        self.setWindowTitle("Найти пользователя")
        self.setModal(True)
        self.setFixedSize(550, 300)
        self.stack_container = QWidget(self)
        self.stack_container.setGeometry(0, 0, 550, 300)

        self.switcher = AnimatedSwitcher(self.stack_container)

        c_w1 = self.create_search_screen()
        c_w2 = self.create_result_screen()

        self.switcher.add_widget(c_w1)
        self.switcher.add_widget(c_w2)
        self.switcher.set_current_index(0)

    def create_search_screen(self):
        screen = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addStretch()
        # ========== Main label ==========
        label = QLabel("Найти пользователя")
        label.setFont(QFont("Inter", 18, QFont.Weight.ExtraBold))
        main_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch()
        # ================================

        # ========== alert label ==========
        self.alert_label = QLabel()
        self.alert_label.setStyleSheet("color: #FF6347;")
        self.alert_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        main_layout.addWidget(self.alert_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # =================================

        # ===== Unique name =====
        def on_text_changed():
            # Если строка не начинается с "@", добавляем его
            if not self.unique_name.text().startswith('@'):
                self.unique_name.setText('@' + self.unique_name.text()[0:])

        self.unique_name = QLineEdit()
        self.unique_name.setPlaceholderText("@Уникальное имя")
        self.unique_name.setStyleSheet(main_screen_line_edit_style)
        self.unique_name.setFont(QFont('Inter', 19, QFont.Weight.Bold))
        self.unique_name.setFixedWidth(300)
        self.unique_name.textChanged.connect(on_text_changed)
        main_layout.addWidget(self.unique_name, alignment=Qt.AlignmentFlag.AlignCenter)
        # ====================

        # ========== Find button ==========
        find_button = StyledAnimatedButton("Найти", def_color="#212121")
        find_button.clicked.connect(lambda: asyncio.create_task(self.search_user_here()))
        main_layout.addWidget(find_button, alignment=Qt.AlignmentFlag.AlignCenter)
        # =================================
        main_layout.addStretch()
        screen.setLayout(main_layout)

        return screen

    def create_result_screen(self):
        screen = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addStretch()
        self.user_widget = SearchScreenProfileWidget()
        self.user_widget.setFixedWidth(300)
        main_layout.addWidget(self.user_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_layout = QHBoxLayout()
        back_button = StyledAnimatedButton("Назад", def_color="#212121", width=200)
        back_button.clicked.connect(lambda: self.switcher.slide_to_index(0, direction="down"))
        btn_layout.addStretch()
        btn_layout.addWidget(back_button)
        self.accept_button = StyledAnimatedButton("Начать чат", btn_style="positive", width=200)
        self.accept_button.clicked.connect(lambda: asyncio.create_task(self.make_positive_action()))
        btn_layout.addWidget(self.accept_button)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)
        main_layout.addStretch()
        screen.setLayout(main_layout)

        return screen

    @pyqtSlot()
    async def search_user_here(self):
        unique_name = self.unique_name.text()
        self.user_data = await search_user(unique_name)
        print(self.user_data)
        self.id = self.user_data.get("id")
        if "request error" in self.user_data:
            print(self.user_data["request error"])
            self.alert_label.setText(self.user_data["request error"])
        else:
            self.alert_label.setText("")
            if self.cur_user == self.user_data.get("id"):
                self.pos_btn = {"text": "Мой профиль", "connect": "open_profile"}
                self.accept_button.edit_text(self.pos_btn["text"])
            else:
                self.pos_btn = {"text": "Открыть чат", "connect": "open_chat"}
                self.accept_button.edit_text(self.pos_btn["text"])
            asyncio.create_task(self.user_widget.input_data(self.user_data, unique_name))
            self.switcher.slide_to_index(1, direction="up")

    async def make_positive_action(self):
        if self.pos_btn["connect"] == "open_profile":
            print("открываю профиль")
        elif self.pos_btn["connect"] == "open_chat":
            data = await create_chat(self.unique_name.text().strip())
            print(data)
            if data["chat_type"] == "new_chat":
                self.item_widget = self.insert_to_list(self.unique_name.text().strip(), "", self.user_widget.avatar_path, data["_id"], self.id)
            self.focus_to_widget(self.id)
            self.open_chat(data["_id"], self.id, self.unique_name.text().strip())
            self.close()