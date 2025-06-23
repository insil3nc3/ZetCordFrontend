import asyncio
import json
import os
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QListWidget, QHBoxLayout, QPushButton, QListWidgetItem, QWidget, \
    QApplication, QSizePolicy, QMessageBox
from PyQt6.QtCore import pyqtSlot, Qt, QEvent, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPalette, QColor, QCursor
from aiortc import RTCSessionDescription, RTCPeerConnection
from qasync import asyncSlot

from backend.delete_token import clear_token_value
from screens.main_screen.call_widget import CallWidget
from screens.main_screen.create_group_widget import CreateGroupWidget
from screens.main_screen.edit_profile_dialog import EditProfileDialog
from screens.main_screen.search_user import UserSearchWidget
from api.profile_actions import get_user_info, download_avatar, get_avatar_path
from api.common import token_manager
from screens.main_screen.chat_widget import ChatWidget
from screens.main_screen.dialog_item_widget import DialogItem
from screens.utils.animate_button import StyledAnimatedButton
from screens.utils.default_avatar import default_ava_path
from screens.utils.incoming_call_widget import IncomingCallWidget
from screens.utils.my_profile_widget import MyProfile
from screens.main_screen.web_socket import WebSocketClient
from screens.utils.screen_style_sheet import screen_style, load_custom_font
from screens.utils.list_utils import configure_list_widget_no_hscroll

class MainWindow(QMainWindow):
    def __init__(self, audio):
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
        self.audio = audio
        self.profile_widget = None
        self.showMaximized()
        self.cur_widget = None
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        self.setStyleSheet(screen_style)

        self.client = WebSocketClient(token=token_manager.get_access_token())
        self.client.message_received.connect(self.handle_ws_message)
        self.client.connected.connect(self.get_init_data)
        self.client.connect()
        # Задаем константы для размеров
        self.DIALOGS_COMPACT_WIDTH = 120
        self.DIALOGS_EXPANDED_WIDTH = 200
        self.GROUPS_COMPACT_WIDTH = self.DIALOGS_COMPACT_WIDTH
        self.GROUPS_EXPANDED_WIDTH = self.DIALOGS_EXPANDED_WIDTH


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
        self.profile_widget = MyProfile(settings_callback=self.settings, exit_callback=self.exit)
        self.cur_user_avatar_path = self.profile_widget.avatar_path
        self.profile_widget.setFixedWidth(320)
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
        self.create_group.clicked.connect(self.create_new_group)

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

        self.search_button.setMinimumWidth(150)
        self.search_button.setMaximumWidth(150)
        self.search_group.setMinimumWidth(90)
        self.search_group.setMaximumWidth(90)
        self.create_group.setMinimumWidth(80)
        self.create_group.setMaximumWidth(80)
        # Изменяем настройки размеров в init:
        self.dialogs_list.setMinimumWidth(self.DIALOGS_COMPACT_WIDTH)
        self.dialogs_list.setMaximumWidth(self.DIALOGS_EXPANDED_WIDTH)
        self.groups_list.setMinimumWidth(self.GROUPS_COMPACT_WIDTH)
        self.groups_list.setMaximumWidth(self.GROUPS_EXPANDED_WIDTH)
        self.groups_list.setFixedWidth(self.GROUPS_COMPACT_WIDTH)
        self.dialogs_list.setFixedWidth(self.DIALOGS_EXPANDED_WIDTH)

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
            self.groups_list.clearSelection()

            self.dialogs_list.setFixedWidth(self.DIALOGS_EXPANDED_WIDTH)
            self.search_button.setFixedWidth(150)
            self.groups_list.setFixedWidth(self.GROUPS_COMPACT_WIDTH)
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
            self.dialogs_list.clearSelection()
            self.dialogs_list.setFixedWidth(self.DIALOGS_COMPACT_WIDTH)
            self.search_button.setFixedWidth(90)
            self.groups_list.setFixedWidth(self.GROUPS_EXPANDED_WIDTH)
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
        if self.dialogs_list:
            self.dialogs_list.clear()
        self.client.send_json({"type": "init"})

    def search_user(self):
        search_user_widget = UserSearchWidget(self.open_chat, self.insert_item_to_dialog_list, self.focus_to_widget, parent=self, cur_user=self.user_start_data['profile_data']["id"], get_init_data=self.get_init_data)
        search_user_widget.show()

    @asyncSlot(str)
    async def handle_ws_message(self, message: str):

        try:

            print(f"📬 Получено WebSocket-сообщение: {message}")
            data = json.loads(message)
            message_type = data.get("type")
            if message_type != "chat_history":
                print(f"Received message: {data}")

            print(f"Тип сообщения: {message_type}")

            if message_type == "init":
                del data["type"]
                print("MainWindow: init data get")
                self.user_start_data = data

                self.dialogs_list.clear()
                self.groups_list.clear()
                await self.fill_dialog_list()
                await self.fill_group_list()
                print("вызов input_data - ",self.user_start_data)
                await self.profile_widget.input_data(self.user_start_data)

            elif message_type == "chat_message":
                if data["chat_id"] == self.cur_chat_id:
                    if self.chat_widget:
                        asyncio.create_task(self.chat_widget.add_message(data["message"]))

            elif message_type == "chat_history":
                print("получено история:", data["type"])
                if data["chat_id"] == self.cur_chat_id:
                    if self.chat_widget:
                        self.chat_widget.show_history(data["messages"])

            elif message_type == "group_message":
                if data["chat_id"] == self.cur_chat_id:
                    if self.chat_widget:
                        asyncio.create_task(self.chat_widget.add_message(data["message"]))

            elif message_type == "offer":
                await self.handle_call_offer(data)

            elif message_type == "answer":
                await self.handle_call_answer(data)

            elif message_type == "ice_candidate":
                await self.handle_ice_candidate(data)

            elif message_type == "call_rejected":
                self.handle_call_rejected(data)

            elif message_type == "end_call":
                self.handle_call_ended(data)

            else:
                print(f"⚠️ Неизвестный тип сообщения: {message_type}")

        except json.JSONDecodeError as e:
            print(f"❌ Ошибка при парсинге JSON: {e}")
            print(f"Сообщение: {message}")
        except Exception as e:
            print(f"❌ Неожиданная ошибка при обработке WebSocket сообщения: {e}")
            import traceback
            traceback.print_exc()

    async def handle_call_offer(self, data):
        """Обработка входящего звонка (offer)"""
        try:
            from_user = data.get("from")
            if not from_user:
                print("❌ Отсутствуют данные звонящего пользователя")
                return

            print(f"📞 Получен оффер от пользователя {from_user.get('nickname', 'Unknown')}")

            # Проверяем, нет ли уже активного входящего звонка
            if self.incoming_call:
                print("⚠️ Входящий звонок уже активен, отклоняем новый")
                # Отправляем отклонение нового звонка
                reject_message = {
                    "type": "call_rejected",
                    "to_user_id": from_user.get("id"),
                    "reason": "busy"
                }
                self.send_via_ws(json.dumps(reject_message))
                return

            # Создаем виджет входящего звонка
            self.incoming_call = IncomingCallWidget(
                data,
                self.audio,
                self.send_via_ws,
                self.call_accept
            )

            # Сохраняем информацию о звонке для дальнейшей обработки
            caller_id = from_user.get("id")
            if not hasattr(self, 'active_calls'):
                self.active_calls = {}

            self.active_calls[caller_id] = {
                "widget": self.incoming_call,
                "data": data,
                "type": "incoming"
            }

            self.incoming_call.show()
            print("✅ Виджет входящего звонка создан и отображен")

        except Exception as e:
            print(f"❌ Ошибка при обработке входящего звонка: {e}")
            import traceback
            traceback.print_exc()

    async def handle_call_answer(self, data):
        """Обработка ответа на звонок (answer)"""
        try:
            print(f"📨 Получен ответ (answer)")
            print(data)
            answer = data.get("answer")
            from_user_id = data.get("from")

            if not answer:
                print("❌ Отсутствует ответ в сообщении")
                return

            print(f"📞 Получен ответ на звонок от пользователя {from_user_id}")

            # Обрабатываем ответ для исходящего звонка
            if self.call_widget and hasattr(self.call_widget, 'call_session') and self.call_widget.call_session:
                try:
                    await self.call_widget.on_answer_received(answer)
                    print("✅ Ответ успешно обработан для исходящего звонка")

                    # Обновляем информацию об активном звонке
                    if hasattr(self, 'active_calls') and from_user_id:
                        self.active_calls[from_user_id] = {
                            "widget": self.call_widget,
                            "call_session": self.call_widget.call_session,
                            "type": "outgoing"
                        }

                except Exception as e:
                    print(f"❌ Ошибка при обработке ответа: {e}")
                    self.call_widget.end_call()
            else:
                print("⚠️ CallWidget или CallSession не инициализированы")

        except Exception as e:
            print(f"❌ Ошибка при обработке ответа на звонок: {e}")
            import traceback
            traceback.print_exc()

    async def handle_ice_candidate(self, data):

        print(f"Received ICE candidate message: {data}")
        from_user_id = data.get("from")
        candidate = data.get("candidate")
        if not candidate:
            print("❌ Отсутствует ICE кандидат в сообщении")
            return
        print(f"🧊 Получен ICE кандидат от пользователя {from_user_id}: {candidate['candidate'][:50]}...")
        """Обработка ICE кандидата"""
        try:
            from_user_id = data.get("from")
            candidate = data.get("candidate")

            if not candidate:
                print("❌ Отсутствует ICE кандидат в сообщении")
                return

            print(f"🧊 Получен ICE кандидат от пользователя {from_user_id}")

            # Флаг успешной обработки
            candidate_processed = False

            # Приоритет 1: Исходящий звонок (call_widget)
            if self.call_widget and hasattr(self.call_widget, 'call_session') and self.call_widget.call_session:
                try:
                    await self.call_widget.call_session.add_ice_candidate(data['candidate'])

                    print("✅ ICE кандидат добавлен в исходящий звонок")
                    candidate_processed = True
                except Exception as e:
                    print(f"❌ Ошибка при добавлении ICE кандидата в исходящий звонок: {e}")

            # Приоритет 2: Входящий звонок (incoming_call)
            if not candidate_processed and self.incoming_call and hasattr(self.incoming_call,
                                                                          'call_session') and self.incoming_call.call_session:
                try:
                    await self.incoming_call.call_session.add_ice_candidate(candidate)
                    print("✅ ICE кандидат добавлен во входящий звонок")
                    candidate_processed = True
                except Exception as e:
                    print(f"❌ Ошибка при добавлении ICE кандидата во входящий звонок: {e}")

            # Приоритет 3: Поиск в активных звонках
            if not candidate_processed and hasattr(self, 'active_calls') and from_user_id:
                call_info = self.active_calls.get(from_user_id)
                if call_info:
                    call_session = call_info.get("call_session")
                    if call_session:
                        try:
                            await call_session.add_ice_candidate(candidate)
                            print("✅ ICE кандидат добавлен через активные звонки")
                            candidate_processed = True
                        except Exception as e:
                            print(f"❌ Ошибка при добавлении ICE кандидата через активные звонки: {e}")

            if not candidate_processed:
                print("⚠️ Нет активной сессии для ICE кандидата - сохраняем для будущего использования")
                # Можно сохранить кандидата для последующего использования
                if not hasattr(self, 'pending_ice_candidates'):
                    self.pending_ice_candidates = {}
                if from_user_id not in self.pending_ice_candidates:
                    self.pending_ice_candidates[from_user_id] = []
                self.pending_ice_candidates[from_user_id].append(candidate)

        except Exception as e:
            print(f"❌ Ошибка при обработке ICE кандидата: {e}")
            import traceback
            traceback.print_exc()

    def handle_call_rejected(self, data):
        """Обработка отклонения звонка"""
        try:
            from_user_id = data.get("from")
            reason = data.get("reason", "rejected")
            print(f"❌ Звонок отклонен пользователем {from_user_id}, причина: {reason}")

            # Завершаем исходящий звонок если он активен
            if self.call_widget:
                self.call_widget.end_call()
                self.call_widget = None

            # Очищаем активные звонки
            if hasattr(self, 'active_calls') and from_user_id in self.active_calls:
                call_info = self.active_calls[from_user_id]
                call_session = call_info.get("call_session")
                if call_session:
                    asyncio.create_task(call_session.close())
                del self.active_calls[from_user_id]

            # Показываем уведомление пользователю
            self.show_call_notification("Звонок отклонен")

        except Exception as e:
            print(f"❌ Ошибка при обработке отклонения звонка: {e}")
            import traceback
            traceback.print_exc()

    def handle_call_ended(self, data):
        """Обработка завершения звонка"""
        try:
            from_user_id = data.get("from_user_id")
            print(f"📴 Получен сигнал завершения звонка от пользователя {from_user_id}")

            # Завершаем исходящий звонок
            if self.call_widget:
                self.call_widget.end_call()
                self.call_widget = None

            # Завершаем входящий звонок
            if self.incoming_call:
                self.incoming_call.call_rejected()
                self.incoming_call = None

            # Очищаем активные звонки
            if hasattr(self, 'active_calls'):
                if from_user_id and from_user_id in self.active_calls:
                    call_info = self.active_calls[from_user_id]
                    call_session = call_info.get("call_session")
                    if call_session:
                        asyncio.create_task(call_session.close())
                    del self.active_calls[from_user_id]
                else:
                    # Если from_user_id не указан, завершаем все активные звонки
                    for user_id, call_info in list(self.active_calls.items()):
                        call_session = call_info.get("call_session")
                        if call_session:
                            asyncio.create_task(call_session.close())
                    self.active_calls.clear()

            # Очищаем ожидающие ICE кандидаты
            if hasattr(self, 'pending_ice_candidates') and from_user_id:
                self.pending_ice_candidates.pop(from_user_id, None)

            print("✅ Звонок успешно завершен и ресурсы очищены")

        except Exception as e:
            print(f"❌ Ошибка при обработке завершения звонка: {e}")
            import traceback
            traceback.print_exc()

    def call_accept(self):
        """Callback при принятии входящего звонка"""
        try:
            print("✅ Звонок принят - переходим в режим разговора")

            # Обновляем статус входящего звонка в активных звонках
            if hasattr(self, 'active_calls') and self.incoming_call:
                for user_id, call_info in self.active_calls.items():
                    if call_info.get("widget") == self.incoming_call:
                        call_info["call_session"] = getattr(self.incoming_call, 'call_session', None)
                        call_info["status"] = "accepted"
                        break

            # Применяем отложенные ICE кандидаты если они есть
            if hasattr(self, 'pending_ice_candidates'):
                for user_id, candidates in self.pending_ice_candidates.items():
                    if user_id in self.active_calls:
                        call_session = self.active_calls[user_id].get("call_session")
                        if call_session:
                            for candidate in candidates:
                                asyncio.create_task(call_session.add_ice_candidate(candidate))
                            print(f"✅ Применено {len(candidates)} отложенных ICE кандидатов для пользователя {user_id}")
                self.pending_ice_candidates.clear()

        except Exception as e:
            print(f"❌ Ошибка при принятии звонка: {e}")
            import traceback
            traceback.print_exc()

    def show_call_notification(self, message):
        """Показать уведомление о звонке"""
        print(f"🔔 Уведомление: {message}")
        # Здесь можно показать системное уведомление или тост
        # Например, используя QSystemTrayIcon или другие методы уведомлений

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
        self.groups_list.clearSelection()
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

    def on_group_item_clicked(self, item):
        self.dialogs_list.clearSelection()
        self.cur_widget = self.groups_list.itemWidget(item)
        if not self.cur_widget:
            return
        try:
            group_id = self.cur_widget.chat_id
            print("group id - ", group_id)
            print("cur_widget.user_id - ", self.cur_widget.user_id)
            self.cur_chat_id = group_id
            print(self.cur_widget.user_id)
            # Для групп используем специальные параметры
            self.open_chat(
                chat_id=group_id,
                receiver_id=self.cur_widget.user_id,  # Для групп нет конкретного получателя
                username=self.cur_widget.username,
                is_group=True
            )
            # Для групп звонок может быть не нужен или реализован по-другому
            self.open_group_call_menu(group_id, self.cur_widget.username, self.cur_widget.ava)
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

    def open_group_call_menu(self, member_ids, member_names, member_avatars):
        if self.call_widget:
            if self.call:
                return
            else:
                self.call_widget.deleteLater()

        self.call_widget = CallWidget(
            receiver_id=member_ids,
            receiver_name=member_names,
            receiver_avatar_path=member_avatars,
            cur_user_info=self.user_start_data["profile_data"],
            audio=self.audio,
            set_calling_status_callback=self.set_calling_status,
            send_via_ws=self.send_via_ws
        )
        self.call_layout.addWidget(self.call_widget)
    def open_chat(self, chat_id, receiver_id, username, is_group=False):
        self.cur_chat_id = chat_id
        if self.chat_widget:
            self.chat_widget.deleteLater()

        data = {"type": "chat_history", "chat_id": chat_id}

        # Модифицируем создание ChatWidget для поддержки групп
        self.chat_widget = ChatWidget(
            user_id=self.user_start_data["profile_data"]["id"],
            chat_id=chat_id,
            receiver_id=receiver_id,
            username=username,
            send_via_ws=self.send_via_ws,
            update_last_msg_callback=self.update_last_msg,
            is_group=is_group
        )
        self.send_via_ws(data)
        self.chat_layout.addWidget(self.chat_widget)

    def update_last_msg(self, text):
        if self.cur_widget:
            self.cur_widget.update_last_message(text)

    def send_via_ws(self, message_data: dict):
        print(f"📤 Отправка WebSocket-сообщения: {message_data}")
        self.client.send_json(message_data)

    async def fill_dialog_list(self):
        self.chats = []
        dialogs = self.user_start_data['chats_data']['chats']
        print("dialogs - ", dialogs)

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
            print("аватар путь:", avatar_path)
            self.widget = self.insert_item_to_dialog_list(
                username=user2.get("nickname"),
                last_msg=last_msg,
                avatar_path=avatar_path,
                chat_id=dialog.get("_id"),
                user_id=self.user2_id
            )
            self.chats.append(user2)
        self.item_widgets = [self.dialogs_list.itemWidget(self.dialogs_list.item(i)) for i in
                             range(self.dialogs_list.count())]
        print("item widgets: ", self.item_widgets)
        print("all contacts: ", self.chats)

    async def fill_group_list(self):
        groups = self.user_start_data["groups_data"]["groups"]
        print("groups - ", groups)
        if not groups:
            return
        for group in groups:
            widget = self.insert_item_to_group_list(
                avatar_path=group["avatar"],
                name=group["name"],
                last_msg=group["last_message"],
                group_id=group["_id"],
                member_ids=group["member_ids"]
            )
            # Добавляем обработчик клика
            item = self.groups_list.item(self.groups_list.count()-1)
            item.widget = widget
        # Подключаем обработчик кликов по группам
        self.groups_list.itemClicked.connect(self.on_group_item_clicked)

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

    def insert_item_to_group_list(self,  avatar_path, name, last_msg, group_id, member_ids):
        avatar = get_avatar_path(avatar_path)
        if avatar == 1:
            ava = default_ava_path
        else:
            ava = avatar
        widget = DialogItem(username=name,
                            last_msg=last_msg["content"] if isinstance(last_msg, dict) else last_msg,
                            avatar_path=ava,
                            chat_id=group_id,
                            user_id=member_ids)
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.groups_list.addItem(item)
        self.groups_list.setItemWidget(item, widget)
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

    def create_new_group(self):
        create_group_widget = CreateGroupWidget(self.user_start_data['profile_data']["id"], parent=self, members=self.chats, send_via_ws=self.send_via_ws)
        create_group_widget.show()

    def exit(self):
        reply = QMessageBox.question(
            self,
            "Подтверждение выхода",
            "Вы действительно хотите выйти из аккаунта?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            clear_token_value()
            QApplication.quit()

    def settings(self):
        settings_window = EditProfileDialog(self.user_start_data["profile_data"].get("nickname"), self.user_start_data["profile_data"].get("unique_name"), self.cur_user_avatar_path, self.send_via_ws)

        settings_window.exec()