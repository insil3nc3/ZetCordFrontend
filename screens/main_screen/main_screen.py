import asyncio
import json
import os
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QListWidget, QHBoxLayout, QPushButton, QListWidgetItem, QWidget, \
    QApplication, QSizePolicy
from PyQt6.QtCore import pyqtSlot, Qt, QEvent, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPalette, QColor, QCursor
from aiortc import RTCSessionDescription, RTCPeerConnection
from qasync import asyncSlot

from backend.audio_manager import AudioManager
from backend.call_session import CallSession
from screens.main_screen.call_widget import CallWidget
from screens.main_screen.search_user import UserSearchWidget
from api.profile_actions import get_user_info, download_avatar
from api.common import token_manager
from screens.main_screen.chat_widget import ChatWidget
from screens.main_screen.dialog_item_widget import DialogItem
from screens.utils.animate_button import StyledAnimatedButton
from screens.utils.incoming_call_widget import IncomingCallWidget
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
        self.call_widget = None
        self.call = False
        self.cur_user_avatar_path = None
        self.incoming_call = None
        self.audio = AudioManager()
        self.showMaximized()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
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
        chats_with_profile_layout.setSpacing(10)
        chats_with_profile_layout.setContentsMargins(0, 10, 0, 0)

        self.profile_widget = MyProfile()
        self.cur_user_avatar_path = self.profile_widget.avatar_path
        self.profile_widget.setFixedWidth(300)
        chats_with_profile_layout.addWidget(self.profile_widget)

        groups_and_dialogs_layout = QHBoxLayout()
        groups_and_dialogs_layout.setSpacing(0)
        groups_and_dialogs_layout.setContentsMargins(0, 0, 0, 0)
        chats_with_profile_layout.addLayout(groups_and_dialogs_layout)

        chats_with_profile_layout_widget = QWidget()
        chats_with_profile_layout_widget.setLayout(chats_with_profile_layout)
        main_layout.addWidget(chats_with_profile_layout_widget, alignment=Qt.AlignmentFlag.AlignLeft)

        groups_layout = QVBoxLayout()
        groups_layout.setContentsMargins(0, 0, 0, 0)
        groups_layout.setSpacing(0)
        groups_and_dialogs_layout.addLayout(groups_layout)

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
                background-color: #110f12;
                border-top-left-radius: 10px;
                border-right: 1px solid #444;
            }    
            """)
        groups_layout.addWidget(self.top_group_container)

        self.groups_list = QListWidget()
        self.create_group = StyledAnimatedButton(text="+", btn_style="positive", font_size=16, height=50, width=80)

        groups_layout.addWidget(self.top_group_container)
        groups_layout.addWidget(self.groups_list)

        self.bottom_group_container = QWidget()
        bottom_group_layout = QHBoxLayout()
        bottom_group_layout.setContentsMargins(0, 10, 0, 10)
        bottom_group_layout.setSpacing(10)
        bottom_group_layout.addStretch()
        bottom_group_layout.addWidget(self.create_group)
        bottom_group_layout.addStretch()
        self.bottom_group_container.setLayout(bottom_group_layout)
        self.bottom_group_container.setStyleSheet("""
            QWidget {
                background-color: #110f12;
                border-bottom-left-radius: 10px;
                border-right: 1px solid #444;
            }    
            """)
        groups_layout.addWidget(self.bottom_group_container)

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
                background-color: #110f12;
                border-top-right-radius: 10px;
                border-left: 1px solid #444;
            }    
            """)

        self.dialogs_list = QListWidget()
        self.dialogs_list.setObjectName("dialogsList")

        dialogs_layout.addWidget(self.top_dialog_container)
        dialogs_layout.addWidget(self.dialogs_list)
        self.dialogs_list.itemClicked.connect(self.on_dialog_item_clicked)

        self.chat_layout = QVBoxLayout()
        main_layout.addLayout(self.chat_layout, 2)

        configure_list_widget_no_hscroll(self.groups_list)
        configure_list_widget_no_hscroll(self.dialogs_list)

        self.groups_list.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.groups_list.viewport().installEventFilter(self)
        self.dialogs_list.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.dialogs_list.viewport().installEventFilter(self)
        self.groups_list.clicked.connect(self.on_groups_list_clicked)
        self.dialogs_list.clicked.connect(self.on_dialogs_list_clicked)

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

        self.dialogs_list.setStyleSheet("""
            QListWidget {
                background-color: #110f12;
                border: none;
                border-left: 1px solid #444;
                margin: 0;
                padding: 0;
                border-bottom-right-radius: 10px;
            }
            QListWidget::item {
                background: transparent;
                border: none;
                margin: 0;
                border-radius: 15px;
                padding: 0;
            }
            QListWidget::item:hover {
                background-color: #4a4a4a;
                border-radius: 20px;
            }
            QListWidget::item:selected {
                background: #383838;
                border-radius: 20px;
                border: none;
            }
            QListWidget::item:pressed {
                background: #6a4a6a;
                border-radius: 20px;
                border: none;
            }
            QListWidget::item:focus {
                outline: none;
                border: none;
            }
        """)

        self.groups_list.setStyleSheet("""
            QListWidget {
                background-color: #110f12;
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

        self.groups_list.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.dialogs_list.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.call_layout = QVBoxLayout()
        main_layout.addLayout(self.call_layout, 1)

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
                    background-color: #110f12;
                    border: none;
                    border-left: 1px solid #444;
                    margin: 0;
                    padding: 0;
                    border-bottom-right-radius: 10px;
                }
                QListWidget::item {
                    background: transparent;
                    border: none;
                    margin: 0;
                    border-radius: 15px;
                    padding: 0;
                }
                QListWidget::item:hover {
                    background-color: #4a4a4a;
                    border-radius: 20px;
                }
                QListWidget::item:selected {
                    background: #383838;
                    border-radius: 20px;
                    border: none;
                }
                QListWidget::item:pressed {
                    background: #6a4a6a;
                    border-radius: 20px;
                    border: none;
                }
                QListWidget::item:focus {
                    outline: none;
                    border: none;
                }
            """)
            self.groups_list.setStyleSheet("""
                QListWidget {
                    background-color: #110f12;
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
                    background-color: #110f12;
                    border-top-right-radius: 10px;
                    border-left: 1px solid #444;
                }    
                """)
            self.top_group_container.setStyleSheet("""
                QWidget {
                    background-color: #110f12;
                    border-top-left-radius: 10px;
                    border-right: 1px solid #444;
                }    
                """)
            self.bottom_group_container.setStyleSheet("""
                QWidget {
                    background-color: #110f12;
                    border-bottom-left-radius: 10px;
                    border-right: 1px solid #444;
                }    
                """)
        else:
            self.dialogs_list.setFixedWidth(120)
            self.search_button.setFixedWidth(90)
            self.groups_list.setFixedWidth(180)
            self.search_group.setFixedWidth(150)
            self.search_group.edit_text("Найти группу")
            self.create_group.setFixedWidth(80)
            self.create_group.edit_text("+")

            self.dialogs_list.setStyleSheet("""
                QListWidget {
                    background-color: #110f12;
                    border: none;
                    border-left: 1px solid #444;
                    margin: 0;
                    padding: 0;
                    border-bottom-right-radius: 10px;
                }
                QListWidget::item {
                    background: transparent;
                    border: none;
                    margin: 0;
                    border-radius: 15px;
                    padding: 0;
                }
                QListWidget::item:hover {
                    background-color: #4a4a4a;
                    border-radius: 20px;
                }
                QListWidget::item:selected {
                    background: #383838;
                    border-radius: 20px;
                    border: none;
                }
                QListWidget::item:pressed {
                    background: #6a4a6a;
                    border-radius: 20px;
                    border: none;
                }
                QListWidget::item:focus {
                    outline: none;
                    border: none;
                }
            """)
            self.groups_list.setStyleSheet("""
                QListWidget {
                    background-color: #110f12;
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
                    background-color: #110f12;
                    border-top-right-radius: 10px;
                    border-left: 1px solid #444;
                }    
                """)
            self.top_group_container.setStyleSheet("""
                QWidget {
                    background-color: #110f12;
                    border-top-left-radius: 10px;
                    border-right: 1px solid #444;
                }    
                """)
            self.bottom_group_container.setStyleSheet("""
                QWidget {
                    background-color: #110f12;
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
        search_user_widget = UserSearchWidget(self.open_chat, self.insert_item_to_dialog_list, self.focus_to_widget, parent=self, cur_user=self.user_start_data['profile_data']["id"])
        search_user_widget.show()

    @asyncSlot(str)
    async def handle_ws_message(self, message: str):
        try:
            print(f"📬 Получено WebSocket-сообщение: {message}")
            data = json.loads(message)
            print(data["type"])
            if data["type"] == "init":
                del data["type"]
                print("MainWindow: init data get")
                self.user_start_data = data
                await self.fill_dialog_list()
                await self.profile_widget.input_data(self.user_start_data)
            elif data["type"] == "chat_message":
                if data["chat_id"] == self.cur_chat_id:
                    if self.chat_widget:
                        self.chat_widget.add_message(data["message"])
            elif data["type"] == "chat_history":
                print("получено история:", data["type"])
                if data["chat_id"] == self.cur_chat_id:
                    if self.chat_widget:
                        self.chat_widget.show_history(data["messages"])
            elif data["type"] == "offer":
                if not self.incoming_call:
                    self.incoming_call = IncomingCallWidget(data, self.audio, self.send_via_ws, self.call_accept)
                    self.incoming_call.show()
            elif data["type"] == "answer":
                sdp = data.get("answer")
                if not sdp:
                    raise ValueError("Ответ не содержит SDP")
                await self.call_widget.on_answer_received(sdp)
                self.call_widget.audio.stop_ringtone()
            elif data["type"] == "ice_candidate":
                if self.call_widget and self.call_session:
                    candidate = data.get("candidate")
                    if candidate:
                        await self.call_widget.on_ice_candidate_received(candidate)
            elif data["type"] == "end_call":
                if self.call_widget:
                    self.call_widget.end_call()
                    self.call_widget.deleteLater()
                    self.call_widget = None
                    self.call = False
        except json.JSONDecodeError as e:
            print("ошибка при получении вебсокет сообщения:", e)
            raise

    def call_accept(self):
        if self.call_widget:
            self.call_widget.audio.stop_ringtone()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if obj == self.groups_list.viewport():
                self.on_groups_list_clicked()
            elif obj == self.dialogs_list.viewport():
                self.on_dialogs_list_clicked()
        return super().eventFilter(obj, event)

    def on_dialog_item_clicked(self, item):
        self.cur_widget = self.dialogs_list.itemWidget(item)
        if not self.cur_widget:
            return
        try:
            chat_id = self.cur_widget.chat_id
            self.cur_chat_id = self.cur_widget.chat_id
            self.open_chat(chat_id, self.cur_widget.user_id, self.cur_widget.username)
            self.open_call_menu(self.cur_widget.user_id, self.cur_widget.username, self.cur_widget.ava, "ababa")
        except AttributeError:
            return

    def open_call_menu(self, receiver_id, receiver_name, receiver_avatar_path, users_data):
        if self.call_widget:
            if self.call:
                return
            else:
                self.call_widget.deleteLater()

        self.call_widget = CallWidget(
            receiver_id=receiver_id,
            receiver_name=receiver_name,
            receiver_avatar_path=receiver_avatar_path,
            cur_user_info=self.user_start_data["profile_data"],
            audio=self.audio,
            set_calling_status_callback=self.set_calling_status,
            send_via_ws=self.send_via_ws
        )
        self.call_layout.addWidget(self.call_widget)

    def open_chat(self, chat_id, receiver_id, username):
        self.cur_chat_id = chat_id
        if self.chat_widget:
            self.chat_widget.deleteLater()
        data = {"type": "chat_history",
                "chat_id": chat_id
                }
        self.chat_widget = ChatWidget(self.user_start_data["profile_data"]["id"], chat_id, receiver_id, username, self.send_via_ws, self.update_last_msg)
        self.send_via_ws(data)
        self.chat_layout.addWidget(self.chat_widget)

    def update_last_msg(self, text):
        if self.cur_widget:
            self.cur_widget.update_last_message(text)

    def send_via_ws(self, message_data: dict):
        self.client.send_json(message_data)

    async def fill_dialog_list(self):
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
            print("скачиваю аватарки...")
            avatar_path = await download_avatar(self.user2_id)
            self.widget = self.insert_item_to_dialog_list(
                username=user2.get("nickname"),
                last_msg=last_msg,
                avatar_path=avatar_path,
                chat_id=dialog.get("_id"),
                user_id=self.user2_id
            )
        self.item_widgets = [self.dialogs_list.itemWidget(self.dialogs_list.item(i)) for i in
                             range(self.dialogs_list.count())]

    def insert_item_to_dialog_list(self, username, last_msg, avatar_path, chat_id, user_id):
        widget = DialogItem(
            username=username,
            last_msg=last_msg,
            avatar_path=avatar_path,
            chat_id=chat_id,
            user_id=user_id
        )
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.dialogs_list.addItem(item)
        self.dialogs_list.setItemWidget(item, widget)
        return widget

    def get_list_index(self, target_id):
        for index in range(self.dialogs_list.count()):
            item = self.dialogs_list.item(index)
            widget = self.dialogs_list.itemWidget(item)
            if widget and getattr(widget, "user_id", None) == target_id:
                return index
            widget.set_default_style()
        return -1

    def focus_to_widget(self, target):
        index = self.get_list_index(target)
        print(index)
        if index != -1:
            self.dialogs_list.setCurrentRow(index)
            item = self.dialogs_list.item(index)
            self.cur_widget = self.dialogs_list.itemWidget(item)

    def set_calling_status(self, calling):
        if calling:
            self.call = True
        else:
            self.call = False