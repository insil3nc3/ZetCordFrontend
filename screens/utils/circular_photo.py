from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath


def create_circular_pixmap(pixmap, size):
    """Создает круглое изображение из квадратного QPixmap."""
    circular_pixmap = QPixmap(size, size)
    circular_pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(circular_pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Создаем круглую маску
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)

    # Рисуем исходное изображение
    scaled_pixmap = pixmap.scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation
    )
    painter.drawPixmap(0, 0, scaled_pixmap)
    painter.end()

    return circular_pixmap