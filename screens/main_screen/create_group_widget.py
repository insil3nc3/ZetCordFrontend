import asyncio
import os
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QFont, QCursor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QWidget, QHBoxLayout, QListWidget, QFileDialog, QListWidgetItem, QCheckBox, QScrollArea
)

from screens.utils.animate_button import StyledAnimatedButton
from screens.utils.animate_text_button import AnimatedButton
from screens.utils.circular_photo import create_circular_pixmap
from screens.utils.default_avatar import default_ava_path
from screens.utils.screen_style_sheet import load_custom_font
from screens.utils.search_screen_profile_widget import SearchScreenProfileWidget
from screens.utils.widgets import main_screen_line_edit_style
from api.profile_actions import upload_avatar

class SelectMembersDialog(QDialog):
    def __init__(self, data=None, preselected_members=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить участников")
        self.setModal(True)
        self.setFixedSize(420, 500)
        self.data = data or []
        self.selected_members = []
        self.preselected_members = preselected_members or []

        layout = QVBoxLayout(self)
        label = QLabel("Выберите участников:")
        layout.addWidget(label)

        # СТИЛЬ ДЛЯ СПИСКА
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border-radius: 12px;
                padding: 5px;
            }
            QListWidget::item {
                background-color: transparent;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: transparent;
            }
        """)
        self.list_widget.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout.addWidget(self.list_widget)

        # КНОПКА ДОБАВЛЕНИЯ
        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.confirm_selection)
        layout.addWidget(self.add_button)

        self.list_widget.itemClicked.connect(self.toggle_checkbox_for_item)

        # Загрузка данных
        asyncio.create_task(self.populate_list_async(self.data))

    async def populate_list_async(self, members):
        for member in members:
            profile_widget = SearchScreenProfileWidget()
            await profile_widget.input_data(member, member.get("unique_name", ""))

            checkbox = QCheckBox()
            checkbox.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 10px;
                    background-color: transparent;
                }
                QCheckBox::indicator {
                    width: 24px;
                    height: 24px;
                    border-radius: 6px; /* Закруглённые углы */
                    border: 2px solid #222222;
                    background-color: #121212; /* Темно-серый */
                }
                QCheckBox::indicator:checked {
                    background-color: #4A3780;
                    border: 2px solid #4A3780;
                    /* Можно добавить иконку галочки, если есть */
                }
            """)

            # Если член уже выбран - чекбокс активен
            if any(m.get("id") == member.get("id") for m in self.preselected_members):
                checkbox.setChecked(True)

            container = QWidget()
            container.setStyleSheet("background-color: transparent;")
            layout = QHBoxLayout(container)
            layout.setContentsMargins(10, 0, 10, 0)
            layout.addWidget(profile_widget)
            layout.addStretch()
            layout.addWidget(checkbox)

            item = QListWidgetItem()
            item.setSizeHint(container.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, {
                "member": member,
                "checkbox": checkbox
            })

            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, container)

    def toggle_checkbox_for_item(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        checkbox: QCheckBox = data["checkbox"]
        checkbox.setChecked(not checkbox.isChecked())

    def confirm_selection(self):
        self.selected_members = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data["checkbox"].isChecked():
                self.selected_members.append(data["member"])
        self.accept()


class CreateGroupWidget(QDialog):
    def __init__(self, cur_user_id, members, send_via_ws,parent=None):
        super().__init__(parent)
        self.cur_user_id = cur_user_id
        self.members = members
        self.selected_members = []
        self.send_via_ws = send_via_ws
        self.setWindowTitle("Создать группу")
        self.setModal(True)
        self.setFixedSize(550, 400)

        font = load_custom_font(12)
        if font:
            self.setFont(font)

        # self.avatar_path = None  # Закомментировал

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addStretch()
        label = QLabel("Создать группу")
        label.setFont(QFont("inter", 24, QFont.Weight.Bold))
        main_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)

        self.avatar = QLabel()
        self.avatar.setFixedSize(120, 120)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet("""
            background-color: #ccc;
            border-radius: 60px;
            border: 2px dashed #888;
        """)
        # self.avatar.mousePressEvent = self.select_avatar  # Закомментировал
        # self.set_avatar()  # Закомментировал
        # top_layout.addWidget(self.avatar)

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)

        def on_text_changed():
            if not self.unique_name_input.text().startswith('@'):
                self.unique_name_input.setText('@' + self.unique_name_input.text()[0:])
        self.unique_name_input = QLineEdit()
        self.unique_name_input.setPlaceholderText("@Уникальное имя")
        self.unique_name_input.setFont(QFont("inter", 20, QFont.Weight.Bold))
        self.unique_name_input.setMinimumHeight(60)
        self.unique_name_input.textChanged.connect(on_text_changed)
        self.unique_name_input.setStyleSheet(main_screen_line_edit_style)
        form_layout.addWidget(self.unique_name_input)

        self.display_name_input = QLineEdit()
        self.display_name_input.setPlaceholderText("Отображаемое имя")
        self.display_name_input.setFont(QFont("inter", 20, QFont.Weight.Bold))
        self.display_name_input.setMinimumHeight(60)
        self.display_name_input.setStyleSheet(main_screen_line_edit_style)
        form_layout.addWidget(self.display_name_input)

        self.add_members_button = AnimatedButton(text="Добавить участников")
        self.add_members_button.clicked.connect(self.open_select_members)
        form_layout.addWidget(self.add_members_button)

        top_layout.addWidget(form_widget)
        main_layout.addWidget(top_widget)
        main_layout.addStretch()
        self.create_button = StyledAnimatedButton(text="Создать")
        self.create_button.clicked.connect(lambda x: asyncio.create_task(self.collect_group_data()))
        main_layout.addWidget(self.create_button, alignment=Qt.AlignmentFlag.AlignCenter)

    # def set_avatar(self, path=None):  # Закомментировал полностью
    #     if path:
    #         pixmap = QPixmap(path)
    #     elif default_ava_path and os.path.exists(default_ava_path):
    #         pixmap = QPixmap(default_ava_path)
    #     else:
    #         pixmap = QPixmap(120, 120)
    #         pixmap.fill(Qt.GlobalColor.lightGray)
    #
    #     circular = create_circular_pixmap(pixmap, 120)
    #     self.avatar.setPixmap(circular)
    #     self.avatar.setScaledContents(True)
    #
    # def select_avatar(self, event):  # Закомментировал полностью
    #     file_dialog = QFileDialog(self)
    #     file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg)")
    #     if file_dialog.exec():
    #         selected = file_dialog.selectedFiles()
    #         if selected:
    #             self.avatar_path = selected[0]
    #             self.set_avatar(self.avatar_path)

    async def collect_group_data(self):
        data = {
            # "avatar_path": self.avatar_path,  # Закомментировал
            "unique_name": self.unique_name_input.text(),
            "nickname": self.display_name_input.text(),
            "members": self.selected_members
        }
        member_ids = []
        for member in self.selected_members:
            member_ids.append(member["id"])
        msg = {"type": "create_group",
               "name": self.display_name_input.text(),
               "unique_name": self.unique_name_input.text(),
               "creator_id": self.cur_user_id,
               "member_ids": member_ids}
        self.send_via_ws(msg)
        # await upload_avatar(self.avatar_path)  # Закомментировал

    def update_selected_members_display(self):
        if hasattr(self, 'selected_scroll_area'):
            self.layout().removeWidget(self.selected_scroll_area)
            self.selected_scroll_area.deleteLater()

        # Контейнер с лэйаутом для имен
        container = QWidget()
        container.setStyleSheet("background-color: #1e1e1e; border-radius: 10px;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(5)

        # Добавляем имена
        for member in self.selected_members:
            label = QLabel(member.get("unique_name", ""))
            label.setFont(QFont("inter", 12, QFont.Weight.Bold))
            label.setStyleSheet("color: white;")
            container_layout.addWidget(label)

        # Обёртка с прокруткой
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Высота строки (около 20-25 пикселей для font-size 14)
        line_height = 22
        min_lines = 1
        max_lines = 4

        # Вычисляем высоту: минимум 2 строки, максимум 4
        # плюс отступы и бордеры (около 20 пикселей)
        height = min(max(len(self.selected_members), min_lines), max_lines) * line_height + 20

        scroll_area.setFixedHeight(height)

        # Вставляем перед кнопкой Создать (последним элементом в main_layout)
        self.layout().insertWidget(self.layout().count() - 1, scroll_area)
        self.selected_scroll_area = scroll_area

    def open_select_members(self):
        dialog = SelectMembersDialog(
            data=self.members,
            preselected_members=self.selected_members,
            parent=self
        )
        if dialog.exec():
            self.selected_members = dialog.selected_members
            self.update_selected_members_display()
