from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QPoint

def animate_transition(switcher, to_index: int, is_back=False):
    stack = switcher.stack
    current_index = stack.currentIndex()
    if current_index == to_index:
        return

    current_widget = stack.widget(current_index)
    next_widget = stack.widget(to_index)

    geo = stack.geometry()
    offset = geo.height()  # <-- вертикальная ось

    # direction: вверх (нажали "Назад") → 1, вниз ("Найти") → -1
    direction = 1 if not is_back else -1

    # Подготовить следующее окно
    next_widget.setGeometry(QRect(0, offset * direction, geo.width(), geo.height()))
    next_widget.show()

    # Анимация текущего экрана (уходит вверх/вниз)
    anim_out = QPropertyAnimation(current_widget, b"pos", stack)
    anim_out.setDuration(500)
    anim_out.setStartValue(current_widget.pos())
    anim_out.setEndValue(current_widget.pos() + QPoint(0, -offset * direction))
    anim_out.setEasingCurve(QEasingCurve.Type.InOutCubic)

    # Анимация входящего экрана (снизу/сверху приходит)
    anim_in = QPropertyAnimation(next_widget, b"pos", stack)
    anim_in.setDuration(500)
    anim_in.setStartValue(QPoint(0, offset * direction))
    anim_in.setEndValue(QPoint(0, 0))
    anim_in.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def on_finished():
        stack.setCurrentIndex(to_index)
        current_widget.move(0, 0)
        next_widget.setGeometry(geo)
        if not is_back:
            switcher.view_stack.append(current_index)

    anim_in.finished.connect(on_finished)
    anim_out.start()
    anim_in.start()
