from PyQt6.QtWidgets import QListWidget
from PyQt6.QtCore import Qt

def configure_list_widget_no_hscroll(widget: QListWidget):
    widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    widget.setWordWrap(True)