from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QTextEdit


class EnterTextEdit(QTextEdit):
    enter_pressed = pyqtSignal()
    height_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.document().contentsChanged.connect(self.update_height)
        self.setMinimumHeight(60)
        self.setMaximumHeight(150)

    def update_height(self):
        doc_height = self.document().size().height()
        new_height = int(doc_height) + 10
        if new_height != self.height():
            self.setFixedHeight(new_height)
            self.height_changed.emit(new_height)

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not e.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.enter_pressed.emit()
        else:
            super().keyPressEvent(e)