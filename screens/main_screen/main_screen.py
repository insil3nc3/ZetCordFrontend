import asyncio
import json

from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QListWidget, QHBoxLayout, QPushButton, QListWidgetItem, QWidget, \
    QApplication, QSizePolicy
from PyQt6.QtCore import pyqtSlot, Qt, QEvent, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPalette, QColor, QCursor
from screens.main_screen.search_user import UserSearchWidget
from api.profile_actions import get_user_info, download_avatar
from api.common import token_manager
from screens.main_screen.chat_widget import ChatWidget
from screens.main_screen.dialog_item_widget import DialogItem
from screens.utils.animate_button import StyledAnimatedButton
from screens.utils.my_profile_widget import MyProfile
from screens.main_screen.web_socket import WebSocketClient
from screens.utils.screen_style_sheet import screen_style, load_custom_font
from screens.utils.list_utils import configure_list_widget_no_hscroll


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user2_id = None
        self.chat_widget = None
        self.user_start_data = None
        self.cur_chat_id = None
        self.active_list = 'dialogs'

        self.showMaximized()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        self.dialogs_list = QListWidget()
        self.groups_list = QListWidget()
        self.setStyleSheet(screen_style)

        self.client = WebSocketClient(token=token_manager.get_access_token())
        self.client.message_received.connect(self.handle_ws_message)
        self.client.connected.connect(self.get_init_data)
        self.client.connect()

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 0, 0, 0))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        QApplication.instance().setPalette(palette)


        font = load_custom_font(12)
        if font:
            self.setFont(font)

        chats_with_profile_layout = QVBoxLayout()
        groups_and_dialogs_layout = QHBoxLayout()
        groups_layout = QVBoxLayout()
        dialogs_layout = QVBoxLayout()

        self.profile_widget = MyProfile()
        self.profile_widget.setFixedWidth(300)
        chats_with_profile_layout.addWidget(self.profile_widget)
        chats_with_profile_layout.addLayout(groups_and_dialogs_layout)
        chats_with_profile_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        chats_with_profile_layout_widget = QWidget()
        chats_with_profile_layout_widget.setLayout(chats_with_profile_layout)
        main_layout.addWidget(chats_with_profile_layout_widget, alignment=Qt.AlignmentFlag.AlignLeft)

        groups_and_dialogs_layout.setSpacing(0)
        groups_and_dialogs_layout.setContentsMargins(0, 0, 0, 0)
        groups_layout.setContentsMargins(0, 0, 0, 0)
        groups_layout.setSpacing(0)
        dialogs_layout.setContentsMargins(0, 0, 0, 0)
        dialogs_layout.setSpacing(0)
        groups_and_dialogs_layout.addLayout(groups_layout)
        groups_and_dialogs_layout.addLayout(dialogs_layout)

        self.search_group = StyledAnimatedButton(text="Найти...", font_size=16, height=42, def_color="#333333")
        self.create_group = StyledAnimatedButton(text="+", btn_style="positive", font_size=16, height=50, width=80)
        groups_layout.addWidget(self.search_group)
        groups_layout.addWidget(self.groups_list)
        # Замените текущий код для bottom_group_container на этот:
        # Удаляем старый код для bottom_group_container и заменяем его на:

        # Основной контейнер для групп
        groups_container = QWidget()
        groups_main_layout = QVBoxLayout()
        groups_main_layout.setContentsMargins(0, 0, 0, 0)
        groups_main_layout.setSpacing(0)

        # Добавляем список групп (будет растягиваться)
        groups_main_layout.addWidget(self.groups_list)

        # Контейнер для кнопки "+" с отступами
        self.bottom_group_container = QWidget()
        bottom_group_layout = QHBoxLayout()
        bottom_group_layout.setContentsMargins(0, 10, 0, 10)  # Отступы сверху и снизу для кнопки
        bottom_group_layout.addStretch()
        bottom_group_layout.addWidget(self.create_group)
        bottom_group_layout.addStretch()
        self.bottom_group_container.setLayout(bottom_group_layout)
        self.bottom_group_container.setStyleSheet("background-color: #171717;")

        # Добавляем контейнер с кнопкой внизу
        groups_main_layout.addWidget(self.bottom_group_container)

        groups_container.setLayout(groups_main_layout)
        groups_layout.addWidget(groups_container)

        self.search_button = QPushButton("Поиск")
        self.search_button.clicked.connect(self.search_user)
        dialogs_layout.addWidget(self.search_button)
        self.dialogs_list.setObjectName("dialogsList")
        dialogs_layout.addWidget(self.dialogs_list)
        self.dialogs_list.itemClicked.connect(self.on_dialog_item_clicked)

        configure_list_widget_no_hscroll(self.groups_list)
        configure_list_widget_no_hscroll(self.dialogs_list)

        self.groups_list.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.groups_list.viewport().installEventFilter(self)
        self.dialogs_list.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.dialogs_list.viewport().installEventFilter(self)
        self.groups_list.clicked.connect(self.on_groups_list_clicked)
        self.dialogs_list.clicked.connect(self.on_dialogs_list_clicked)

        self.chat_layout = QVBoxLayout()
        main_layout.addLayout(self.chat_layout)
        main_layout.addStretch()

        # Set initial sizes directly to prevent incorrect state
        self.dialogs_list.setMinimumWidth(200)
        self.dialogs_list.setMaximumWidth(200)
        self.search_button.setMinimumWidth(200)
        self.search_button.setMaximumWidth(200)
        self.groups_list.setMinimumWidth(100)
        self.groups_list.setMaximumWidth(100)
        self.search_group.setMinimumWidth(100)
        self.search_group.setMaximumWidth(100)
        self.create_group.setMinimumWidth(80)
        self.create_group.setMaximumWidth(80)

        self.dialogs_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                border: none;
                padding: 0;
                margin: 0;
            }
            QListWidget::item:hover {
                background-color: #4a4a4a;
            }
            QListWidget::item:selected {
                background-color: #333333;
            }
        """)

        self.groups_list.setStyleSheet("""
            QListWidget {
                background-color: #171717;
                border: none;
                padding: 0;
                margin: 0;
            }
            QListWidget::item:hover {
                background-color: #4a4a4a;
            }
            QListWidget::item:selected {
                background-color: #333333;
            }
        """)
        # Для groups_layout и dialogs_layout
        groups_layout.setContentsMargins(0, 0, 0, 0)
        groups_layout.setSpacing(0)
        dialogs_layout.setContentsMargins(0, 0, 0, 0)
        dialogs_layout.setSpacing(0)

        # Для chats_with_profile_layout
        chats_with_profile_layout.setContentsMargins(0, 0, 0, 0)
        chats_with_profile_layout.setSpacing(0)
        dialogs_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.dialogs_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.groups_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.groups_list.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.dialogs_list.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        # В методе __init__ после создания списков добавьте:
        self.groups_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.dialogs_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def set_active_list(self, list_name):
        if list_name == self.active_list:
            return
        self.active_list = list_name

        if list_name == 'dialogs':
            self.dialogs_list.setFixedWidth(200)
            self.search_button.setFixedWidth(200)
            self.groups_list.setFixedWidth(100)
            self.search_group.setFixedWidth(100)
            self.search_group.edit_text("Найти...")
            self.create_group.setFixedWidth(80)
            self.create_group.edit_text("+")

            self.dialogs_list.setStyleSheet("""
                QListWidget {
                    background-color: #2b2b2b;
                    border: none;
                    padding: 0;
                    margin: 0;
                }
                QListWidget::item:hover {
                    background-color: #4a4a4a;
                }
                QListWidget::item:selected {
                    background-color: #333333;
                }
            """)
            self.groups_list.setStyleSheet("""
                QListWidget {
                    background-color: #171717;
                    border: none;
                    padding: 0;
                    margin: 0;
                }
                QListWidget::item:hover {
                    background-color: #2a2a2a;
                }
                QListWidget::item:selected {
                    background-color: #333333;
                }
            """)
            self.bottom_group_container.setStyleSheet("background-color: #171717;")
        else:
            self.dialogs_list.setFixedWidth(100)
            self.search_button.setFixedWidth(100)
            self.groups_list.setFixedWidth(200)
            self.search_group.setFixedWidth(200)
            self.search_group.edit_text("Найти группу")
            self.create_group.setFixedWidth(80)
            self.create_group.edit_text("+")

            self.dialogs_list.setStyleSheet("""
                QListWidget {
                    background-color: #171717;
                    border: none;
                    padding: 0;
                    margin: 0;
                }
                QListWidget::item:hover {
                    background-color: #2a2a2a;
                }
                QListWidget::item:selected {
                    background-color: #333333;
                }
            """)
            self.groups_list.setStyleSheet("""
                QListWidget {
                    background-color: #2b2b2b;
                    border: none;
                    padding: 0;
                    margin: 0;
                }
                QListWidget::item:hover {
                    background-color: #4a4a4a;
                }
                QListWidget::item:selected {
                    background-color: #333333;
                }
            """)
            self.bottom_group_container.setStyleSheet("background-color: #2b2b2b;")

    @pyqtSlot()
    def on_groups_list_clicked(self):
        self.set_active_list('groups')
        for i in range(self.dialogs_list.count()):
            item = self.dialogs_list.item(i)
            widget = self.dialogs_list.itemWidget(item)
            if widget:
                widget.set_compact_mode(True)

    @pyqtSlot()
    def on_dialogs_list_clicked(self, index=None):
        self.set_active_list('dialogs')
        for i in range(self.dialogs_list.count()):
            item = self.dialogs_list.item(i)
            widget = self.dialogs_list.itemWidget(item)
            if widget:
                widget.set_compact_mode(False)

    def get_init_data(self):
        self.client.send_json({"type": "init"})

    def search_user(self):
        search_user_widget = UserSearchWidget(self, self.user_start_data['profile_data']["id"])
        search_user_widget.show()

    @pyqtSlot(str)
    def handle_ws_message(self, message: str):
        try:
            data = json.loads(message)
            if data["type"] == "init":
                del data["type"]
                self.user_start_data = data
                asyncio.create_task(self.fill_dialog_list())
                asyncio.create_task(self.profile_widget.input_data(self.user_start_data))
            elif data["type"] == "chat_message":
                if data["chat_id"] == self.cur_chat_id:
                    if self.chat_widget:
                        self.chat_widget.append_message(data)
            elif data["type"] == "chat_history":
                if data["chat_id"] == self.cur_chat_id:
                    if self.chat_widget:
                        self.chat_widget.show_history(data["messages"])
        except json.JSONDecodeError as e:
            print("ошибка при получении вебсокет сообщения:", e)

    def eventFilter(self, obj, event):
        # ========== Обработка кликов по пустой области ==========
        if event.type() == QEvent.Type.MouseButtonPress:
            if obj == self.groups_list.viewport():
                # print("Groups list clicked (empty area)")
                self.on_groups_list_clicked()
            elif obj == self.dialogs_list.viewport():
                # print("Dialogs list clicked (empty area)")
                self.on_dialogs_list_clicked()
        return super().eventFilter(obj, event)
        # ==============================

    def on_dialog_item_clicked(self, item):
        # ========== Обработка клика по элементу dialogs_list ==========
        cur_widget = self.dialogs_list.itemWidget(item)
        if not cur_widget:
            # print("Ошибка: Виджет не найден для элемента")
            return
        try:
            chat_id = cur_widget.chat_id
            if self.chat_widget:
                self.chat_widget.deleteLater()
            self.cur_chat_id = cur_widget.chat_id
            data = {"type": "chat_history",
                    "chat_id": self.cur_chat_id
                    }
            self.send_via_ws(data)
            self.chat_widget = ChatWidget(self.user_start_data["profile_data"]["id"], chat_id, cur_widget.user_id, self.send_via_ws)
            self.chat_layout.addWidget(self.chat_widget)
        except AttributeError:
            # print("Ошибка: Атрибут chat_id не найден в виджете")
            return

    def send_via_ws(self, message_data: dict):
        self.client.send_json(message_data)

    async def fill_dialog_list(self):
        # ========== Заполнение dialogs_list ==========
        dialogs = self.user_start_data['chats_data']['chats']
        if not dialogs:
            return
        for dialog in dialogs:
            last_msg = ""
            if dialog.get("last_message") is not None:
                last_msg = dialog["last_message"].get("content")
            if self.user_start_data["profile_data"].get("id") == dialog.get("user1_id"):
                self.user2_id = dialog.get("user2_id")
            else:
                self.user2_id = dialog.get("user1_id")
            user2 = await get_user_info(self.user2_id)
            avatar_path = await download_avatar(self.user2_id)
            widget = DialogItem(
                username=user2.get("nickname"),
                last_msg=last_msg,
                avatar_path=avatar_path,
                chat_id=dialog.get("_id"),
                user_id=self.user2_id
            )
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.dialogs_list.addItem(item)
            self.dialogs_list.setItemWidget(item, widget)
        # ==============================
        # Сохраняем ссылку на виджеты для управления
        self.item_widgets = [self.dialogs_list.itemWidget(self.dialogs_list.item(i)) for i in
                             range(self.dialogs_list.count())]

        # Подключаем обработчик выделения
        self.dialogs_list.currentItemChanged.connect(self.on_item_selected)

    def on_item_selected(self, current, previous):
        for i in range(self.dialogs_list.count()):
            item = self.dialogs_list.item(i)
            widget = self.dialogs_list.itemWidget(item)
            if item is current:
                widget.set_selected_style()
            else:
                widget.set_default_style()