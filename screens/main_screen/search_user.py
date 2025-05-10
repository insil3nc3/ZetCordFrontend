import asyncio

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from api.profile_actions import search_user
from screens.utils.animate_button import StyledAnimatedButton
from screens.utils.screen_style_sheet import screen_style, load_custom_font
from screens.utils.widgets import line_edit_style, main_screen_line_edit_style
from screens.main_screen.search_screen_switcher import AnimatedSwitcher


class UserSearchWidget(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_data = None
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
        back_button = StyledAnimatedButton("Назад", def_color="#212121")
        back_button.clicked.connect(lambda: self.switcher.slide_to_index(0, direction="down"))
        main_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)
        screen.setLayout(main_layout)

        return screen

    @pyqtSlot()
    async def search_user_here(self):
        unique_name = self.unique_name.text()
        self.user_data = await search_user(unique_name)
        print(self.user_data)
        self.switcher.slide_to_index(1, direction="up")