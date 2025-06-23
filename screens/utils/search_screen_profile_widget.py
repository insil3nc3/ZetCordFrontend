from PyQt6.QtCore import Qt, QSize, QRectF
from PyQt6.QtGui import QPixmap, QFont, QPainter, QPainterPath, QLinearGradient, QColor
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout
from api.profile_actions import get_current_user, download_avatar
from screens.utils.circular_photo import create_circular_pixmap
from screens.utils.default_avatar import default_ava_path
from screens.utils.screen_style_sheet import load_custom_font


class SearchScreenProfileWidget(QWidget):
    def __init__(self, width=None, height=None):
        super().__init__()

        # Apply custom font
        font = load_custom_font(12)
        if font:
            self.setFont(font)

        # Set fixed size only if width and height are provided
        if width is not None and height is not None:
            self.setFixedSize(width, height)
        else:
            self.setMinimumSize(300, 90)  # Default minimum size for flexibility

        # Set gradient background via stylesheet
        self.setStyleSheet("""
            SearchScreenProfileWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4A3780, stop:1 #3C2A91
                );
                border-radius: 10px;
            }
        """)

        # Create main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # Margins for padding
        main_layout.setSpacing(10)  # Space between avatar and text

        # Avatar
        self.avatar = QLabel(self)
        self.avatar.setFixedSize(70, 70)  # Fixed size for avatar to maintain circular shape
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet("background: transparent;")

        # Text layout for username and unique name
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)  # Space between username and unique name

        # Username
        self.username = QLabel("Username", self)
        self.username.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        self.username.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.username.setStyleSheet("background: transparent; color: white;")

        # Unique name
        self.unique_name = QLabel("", self)
        self.unique_name.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.unique_name.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.unique_name.setStyleSheet("background: transparent; color: gray;")

        # Add labels to text layout
        text_layout.addWidget(self.username)
        text_layout.addWidget(self.unique_name)
        text_layout.addStretch()  # Push text to top

        # Add widgets to main layout
        main_layout.addWidget(self.avatar)
        main_layout.addLayout(text_layout)
        main_layout.addStretch()  # Allow widget to expand horizontally if needed

        self.setLayout(main_layout)

    def sizeHint(self):
        return QSize(300, 100)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        outer_rect = QRectF(self.rect())
        border_radius = 10
        border_thickness = 3

        # Gradient for border
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#4C2A57"))
        gradient.setColorAt(1, QColor("#7A4165"))

        outer_path = QPainterPath()
        outer_path.addRoundedRect(outer_rect, border_radius, border_radius)

        inner_rect = outer_rect.adjusted(
            border_thickness, border_thickness,
            -border_thickness, -border_thickness
        )
        inner_path = QPainterPath()
        inner_path.addRoundedRect(inner_rect, border_radius - 1, border_radius - 1)

        border_path = outer_path.subtracted(inner_path)
        painter.fillPath(border_path, gradient)
        painter.fillPath(inner_path, QColor("#121212"))

        painter.end()

    async def input_data(self, data, unique_name):
        self.avatar_path = await download_avatar(data.get("id"))
        pixmap = QPixmap(self.avatar_path if self.avatar_path else default_ava_path)

        # Create circular pixmap
        circular_pixmap = create_circular_pixmap(pixmap, 70)
        self.avatar.setPixmap(circular_pixmap)

        self.username.setText(data.get("nickname", "Имя"))
        self.unique_name.setText(unique_name)

    def sync_input_data(self, data):
        self.avatar_path = data["avatar_path"]
        pixmap = QPixmap(self.avatar_path if self.avatar_path else default_ava_path)

        # Create circular pixmap
        circular_pixmap = create_circular_pixmap(pixmap, 70)
        self.avatar.setPixmap(circular_pixmap)

        self.username.setText(data.get("nickname", "Имя"))