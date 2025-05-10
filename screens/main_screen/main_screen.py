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
        # ========== Initialize variables ==========
        self.user2_id = None
        self.chat_widget = None
        self.user_start_data = None
        self.cur_chat_id = None
        self.active_list = 'dialogs'
        # =========================================

        self.showMaximized()

        # ========== Main window setup ==========
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        self.setStyleSheet(screen_style)
        # ======================================

        # ========== WebSocket client ==========
        self.client = WebSocketClient(token=token_manager.get_access_token())
        self.client.message_received.connect(self.handle_ws_message)
        self.client.connected.connect(self.get_init_data)
        self.client.connect()
        # =====================================

        # ========== Application palette ==========
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 0, 0, 0))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        QApplication.instance().setPalette(palette)
        # ========================================

        # ========== Font setup ==========
        font = load_custom_font(12)
        if font:
            self.setFont(font)
        # ===============================

        # ========== Profile and chats container ==========
        chats_with_profile_layout = QVBoxLayout()
        chats_with_profile_layout.setSpacing(10)  # Добавлен отступ сверху списков
        chats_with_profile_layout.setContentsMargins(0, 10, 0, 0)  # Отступ сверху

        self.profile_widget = MyProfile()
        self.profile_widget.setFixedWidth(300)
        chats_with_profile_layout.addWidget(self.profile_widget)

        groups_and_dialogs_layout = QHBoxLayout()
        groups_and_dialogs_layout.setSpacing(0)
        groups_and_dialogs_layout.setContentsMargins(0, 0, 0, 0)
        chats_with_profile_layout.addLayout(groups_and_dialogs_layout)

        chats_with_profile_layout_widget = QWidget()
        chats_with_profile_layout_widget.setLayout(chats_with_profile_layout)
        main_layout.addWidget(chats_with_profile_layout_widget, alignment=Qt.AlignmentFlag.AlignLeft)
        # ================================================

        # ========== Groups section ==========
        groups_layout = QVBoxLayout()
        groups_layout.setContentsMargins(0, 0, 0, 0)
        groups_layout.setSpacing(0)
        groups_and_dialogs_layout.addLayout(groups_layout)

        # Кнопка "Найти..." с аналогичными настройками
        self.search_group = StyledAnimatedButton(
            text="Найти...",
            font_size=14,
            height=35,
            def_color="#333333",
            width=90,
            border_radius=14
        )
        self.top_group_container = QWidget()
        top_group_layout = QHBoxLayout()
        top_group_layout.setContentsMargins(0, 10, 0, 10)
        top_group_layout.setSpacing(10)
        top_group_layout.addStretch()
        top_group_layout.addWidget(self.search_group)
        top_group_layout.addStretch()
        self.top_group_container.setLayout(top_group_layout)
        self.top_group_container.setStyleSheet("""
            QWidget {
                background-color: #1c1c1c;
                border-top-left-radius: 10px;
                border-right: 1px solid #444;
            }    
            """)
        groups_layout.addWidget(self.top_group_container)

        self.groups_list = QListWidget()


        self.create_group = StyledAnimatedButton(text="+", btn_style="positive", font_size=16, height=50, width=80)

        groups_layout.addWidget(self.top_group_container)
        groups_layout.addWidget(self.groups_list)

        # Bottom container with "+" button
        self.bottom_group_container = QWidget()
        bottom_group_layout = QHBoxLayout()
        bottom_group_layout.setContentsMargins(0, 10, 0, 10)  # Отступы сверху и снизу для кнопки
        bottom_group_layout.setSpacing(10)
        bottom_group_layout.addStretch()
        bottom_group_layout.addWidget(self.create_group)
        bottom_group_layout.addStretch()
        self.bottom_group_container.setLayout(bottom_group_layout)
        self.bottom_group_container.setStyleSheet("""
            QWidget {
                background-color: #1c1c1c;
                border-bottom-left-radius: 10px;
                border-right: 1px solid #444;
            }    
            """)
        groups_layout.addWidget(self.bottom_group_container)
        # ===================================

        # ========== Dialogs section ==========
        dialogs_layout = QVBoxLayout()
        dialogs_layout.setContentsMargins(0, 0, 0, 0)
        dialogs_layout.setSpacing(0)
        groups_and_dialogs_layout.addLayout(dialogs_layout)

        self.search_button = StyledAnimatedButton(
            text="Поиск",
            font_size=14,
            height=35,
            def_color="#333333",
            width=90,
            border_radius=14
        )
        self.search_button.clicked.connect(self.search_user)
        self.top_dialog_container = QWidget()
        top_dialog_layout = QHBoxLayout()
        top_dialog_layout.setContentsMargins(0, 10, 0, 10)
        top_dialog_layout.setSpacing(10)
        top_dialog_layout.addStretch()
        top_dialog_layout.addWidget(self.search_button)
        top_dialog_layout.addStretch()
        self.top_dialog_container.setLayout(top_dialog_layout)
        self.top_dialog_container.setStyleSheet("""
            QWidget {
                background-color: #1c1c1c;
                border-top-right-radius: 10px;
                border-left: 1px solid #444;
            }    
            """)



        self.dialogs_list = QListWidget()
        self.dialogs_list.setObjectName("dialogsList")

        dialogs_layout.addWidget(self.top_dialog_container)
        dialogs_layout.addWidget(self.dialogs_list)
        self.dialogs_list.itemClicked.connect(self.on_dialog_item_clicked)
        # ====================================

        # ========== Chat area ==========
        self.chat_layout = QVBoxLayout()
        main_layout.addLayout(self.chat_layout)
        main_layout.addStretch()
        # ==============================

        # ========== List widgets configuration ==========
        configure_list_widget_no_hscroll(self.groups_list)
        configure_list_widget_no_hscroll(self.dialogs_list)

        self.groups_list.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.groups_list.viewport().installEventFilter(self)
        self.dialogs_list.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.dialogs_list.viewport().installEventFilter(self)
        self.groups_list.clicked.connect(self.on_groups_list_clicked)
        self.dialogs_list.clicked.connect(self.on_dialogs_list_clicked)
        # ===============================================

        # ========== Size constraints ==========
        self.dialogs_list.setMinimumWidth(200)
        self.dialogs_list.setMaximumWidth(200)
        self.search_button.setMinimumWidth(150)
        self.search_button.setMaximumWidth(150)
        self.groups_list.setMinimumWidth(100)
        self.groups_list.setMaximumWidth(100)
        self.search_group.setMinimumWidth(90)
        self.search_group.setMaximumWidth(90)
        self.create_group.setMinimumWidth(80)
        self.create_group.setMaximumWidth(80)
        # =====================================

        # ========== Stylesheets ==========
        self.dialogs_list.setStyleSheet("""
            QListWidget {
                background-color: #1c1c1c;
                border: none;
                border-left: 1px solid #444;
                margin: 0;
                padding: 0;
                border-bottom-right-radius: 10px;
            }
            QListWidget::item:hover {
                background-color: #4a4a4a;
                border-radius:15px;
            }
            QListWidget::item:selected {
                background: #855685;
                border-radius: 20px;
            }
            QListWidget::item {
                background: transparent;
            }
            QListWidget::item:pressed {
                background-color: none;
            }
            QListWidget::item:focus {
                outline: none;
            }
        """)

        self.groups_list.setStyleSheet("""
            QListWidget {
                background-color: #1c1c1c;
                border: none;
                border-right: 1px solid #444;
                margin: 0;
                padding: 0;
            }
            QListWidget::item:hover {
                background-color: #4a4a4a;
                border-radius:15px;
            }
            QListWidget::item:selected {
                background: #855685;
                border-radius: 20px;
            }
            QListWidget::item:focus {
                outline: none;
            }
        """)
        # ================================

        # ========== Cursors ==========
        self.groups_list.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.dialogs_list.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        # =============================

    def set_active_list(self, list_name):
        if list_name == self.active_list:
            return
        self.active_list = list_name

        if list_name == 'dialogs':
            self.dialogs_list.setFixedWidth(200)
            self.search_button.setFixedWidth(150)
            self.groups_list.setFixedWidth(100)
            self.search_group.setFixedWidth(90)
            self.search_group.edit_text("Найти...")
            self.create_group.setFixedWidth(80)
            self.create_group.edit_text("+")

            self.dialogs_list.setStyleSheet("""
                QListWidget {
                    background-color: #1c1c1c;
                    border: none;
                    border-left: 1px solid #444;
                    margin: 0;
                    padding: 0;
                    border-bottom-right-radius: 10px;
                }
                QListWidget::item:hover {
                    background-color: #4a4a4a;
                    border-radius:15px;
                }
                QListWidget::item:selected {
                    background: #855685;
                    border-radius:20px;
                }
                QListWidget::item {
                    background: transparent;
                }
                QListWidget::item:pressed {
                    background-color: none;
                }
                QListWidget::item:focus {
                    outline: none;
                }
            """)
            self.groups_list.setStyleSheet("""
                QListWidget {
                    background-color: #1c1c1c;
                    border: none;
                    border-right: 1px solid #444;
                    padding: 0;
                    margin: 0;
                }
                QListWidget::item:hover {
                    background-color: #2a2a2a;
                    border-radius:15px;
                }
                QListWidget::item:selected {
                    background: #855685;
                    border-radius:15px;
                }
            """)
            self.top_dialog_container.setStyleSheet("""
                QWidget {
                    background-color: #1c1c1c;
                    border-top-right-radius: 10px;
                    border-left: 1px solid #444;
                }    
                """)
            self.top_group_container.setStyleSheet("""
                QWidget {
                    background-color: #1c1c1c;
                    border-top-left-radius: 10px;
                    border-right: 1px solid #444;
                }    
                """)
            self.bottom_group_container.setStyleSheet("""
                QWidget {
                    background-color: #1c1c1c;
                    border-bottom-left-radius: 10px;
                    border-right: 1px solid #444;
                }    
                """)
        else:
            self.dialogs_list.setFixedWidth(100)
            self.search_button.setFixedWidth(90)
            self.groups_list.setFixedWidth(200)
            self.search_group.setFixedWidth(150)
            self.search_group.edit_text("Найти группу")
            self.create_group.setFixedWidth(80)
            self.create_group.edit_text("+")

            self.dialogs_list.setStyleSheet("""
                QListWidget {
                    background-color: #1c1c1c;
                    border: none;
                    border-left: 1px solid #444;
                    margin: 0;
                    padding: 0;
                    border-bottom-right-radius: 10px;
                }
                QListWidget::item:hover {
                    background-color: #4a4a4a;
                    border-radius:15px;
                }
                QListWidget::item:selected {
                    background: #855685;
                    border-radius:20px;
                }
                QListWidget::item {
                    background: transparent;
                }
                QListWidget::item:pressed {
                    background-color: none;
                }
                QListWidget::item:focus {
                    outline: none;
                }
            """)
            self.groups_list.setStyleSheet("""
                QListWidget {
                    background-color: #1c1c1c;
                    border: none;
                    padding: 0;
                    margin: 0;
                    border-right: 1px solid #444;
                }
                QListWidget::item:hover {
                    background-color: #4a4a4a;
                    border-radius:15px;
                }
                QListWidget::item:selected {
                    background: #855685;
                    border-radius:15px;
                }
            """)
            self.top_dialog_container.setStyleSheet("""
                QWidget {
                    background-color: #1c1c1c;
                    border-top-right-radius: 10px;
                    border-left: 1px solid #444;
                }    
                """)
            self.top_group_container.setStyleSheet("""
                QWidget {
                    background-color: #1c1c1c;
                    border-top-left-radius: 10px;
                    border-right: 1px solid #444;
                }    
                """)
            self.bottom_group_container.setStyleSheet("""
                QWidget {
                    background-color: #1c1c1c;
                    border-bottom-left-radius: 10px;
                    border-right: 1px solid #444;
                }    
                """)

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
        # self.dialogs_list.currentItemChanged.connect(self.on_item_selected)

    def on_item_selected(self, current, previous):
        for i in range(self.dialogs_list.count()):
            item = self.dialogs_list.item(i)
            widget = self.dialogs_list.itemWidget(item)
            if item is current:
                widget.set_selected_style()
            else:
                widget.set_default_style()