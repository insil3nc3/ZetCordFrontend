import os
from PyQt6.QtGui import QFontDatabase, QFont

def load_custom_font(font_size: int = 12) -> QFont | None:
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(cur_dir, "..", "..", "font", "static", "Inter_18pt-Regular.ttf")

    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id != -1:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        return QFont(font_family, font_size)
    else:
        print("❌ Ошибка загрузки шрифта:", font_path)
        return None

screen_style = """
    background-color: #171418;
    color: #E8E8E8;
    font-family: 'Inter', sans-serif;
"""
