
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect


def animate_transition(self, to_index: int, is_back=False):
    current_index = self.stack.currentIndex()
    if current_index == to_index:
        return

    current_widget = self.stack.widget(current_index)
    next_widget = self.stack.widget(to_index)
    geo = self.stack.geometry()
    offset = geo.width()

    direction = 1 if is_back else -1

    next_widget.setGeometry(QRect(offset * direction, 0, geo.width(), geo.height()))
    next_widget.show()

    self.anim_out = QPropertyAnimation(current_widget, b"pos", self)
    self.anim_out.setDuration(1000)
    self.anim_out.setStartValue(current_widget.pos())
    self.anim_out.setEndValue(current_widget.pos() + QPoint(offset * direction, 0))
    self.anim_out.setEasingCurve(QEasingCurve.Type.InOutCubic)

    self.anim_in = QPropertyAnimation(next_widget, b"pos", self)
    self.anim_in.setDuration(1000)
    self.anim_in.setStartValue(QPoint(-offset * direction, 0))
    self.anim_in.setEndValue(QPoint(0, 0))
    self.anim_in.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def on_animation_finished():
        self.stack.setCurrentIndex(to_index)
        current_widget.move(0, 0)
        next_widget.setGeometry(geo)
        if not is_back:
            self.view_stack.append(current_index)  # Добавляем текущий в историю

    self.anim_in.finished.connect(on_animation_finished)
    self.anim_out.start()
    self.anim_in.start()