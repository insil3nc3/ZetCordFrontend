line_edit_style_alert = """
    QLineEdit {
        font-size: 18px;          /* Увеличиваем размер шрифта */
        height: 30px;             /* Увеличиваем высоту поля ввода */
        padding: 10px;            /* Добавляем отступы внутри поля */
        border-radius: 6px;       /* Скругляем углы */
        border: 2px solid #FF6347; /* Цвет и толщина границы по умолчанию */
        background-color: #333333; /* Цвет фона */
        color: #E8E8E8;           /* Цвет текста */
    }

    QLineEdit:focus {
        border: 2px solid #FF6347;   /* Цвет рамки при фокусе (фиолетовый) */
    }
"""

line_edit_style = """
    QLineEdit {
        font-size: 18px;          /* Увеличиваем размер шрифта */
        height: 30px;             /* Увеличиваем высоту поля ввода */
        padding: 10px;            /* Добавляем отступы внутри поля */
        border-radius: 6px;       /* Скругляем углы */
        border: 2px solid #121212; /* Цвет и толщина границы по умолчанию */
        background-color: #333333; /* Цвет фона */
        color: #E8E8E8;           /* Цвет текста */
    }

    QLineEdit:focus {
        border: 2px solid #9B4DCA;   /* Цвет рамки при фокусе (фиолетовый) */
    }
"""

main_screen_line_edit_style = """
    QLineEdit {
        font-size: 18px;          /* Увеличиваем размер шрифта */
        height: 30px;             /* Увеличиваем высоту поля ввода */
        padding: 10px;            /* Добавляем отступы внутри поля */
        border-radius: 6px;       /* Скругляем углы */
        border: 2px solid #121212; /* Цвет и толщина границы по умолчанию */
        background-color: #1c1c1c; /* Цвет фона */
        color: #E8E8E8;           /* Цвет текста */
    }

    QLineEdit:focus {
        border: 2px solid #9B4DCA;   /* Цвет рамки при фокусе (фиолетовый) */
    }
"""

button_style = """
    QPushButton {
        font-size: 18px;
        height: 30px;
        padding: 10px;
        border-radius: 6px;
        background-color: #333333; /* Графитовый темный фон */
        color: #9B4DCA;             /* Светло-фиолетовый текст */
        border: 2px solid transparent;
    }

    QPushButton:hover {
        background-color: #9B4DCA; /* Средний фиолетовый фон при наведении */
        border: 2px solid #9B4DCA;  /* Фиолетовая граница при наведении */
        color: #FFFFFF;             /* Белый текст при наведении */
    }

    QPushButton:pressed {
        background-color: #2C1D6A;  /* Темный фиолетовый фон при нажатии */
        color: #E1A9FF;             /* Светлый фиолетовый текст */
        border: 2px solid #9B4DCA;  /* Фиолетовая граница */
    }
"""

main_screen_button_style = """
    QPushButton {
        font-size: 18px;
        height: 30px;
        padding: 10px;
        border-radius: 6px;
        background-color: #0d0d0d; /* Графитовый темный фон */
        color: #9B4DCA;             /* Светло-фиолетовый текст */
        border: 2px solid transparent;
    }

    QPushButton:hover {
        background-color: #9B4DCA; /* Средний фиолетовый фон при наведении */
        border: 2px solid #9B4DCA;  /* Фиолетовая граница при наведении */
        color: #FFFFFF;             /* Белый текст при наведении */
    }

    QPushButton:pressed {
        background-color: #2C1D6A;  /* Темный фиолетовый фон при нажатии */
        color: #E1A9FF;             /* Светлый фиолетовый текст */
        border: 2px solid #9B4DCA;  /* Фиолетовая граница */
    }
"""

code_confirm_style_sheet = """
    QLineEdit { 
        background: transparent;
        color: #FFFFFF;
        border: 2px solid #555555;
        border-radius: 8px;
        padding-left: 10px;         /* Добавляем отступ слева */
        letter-spacing: 10px;       /* Расстояние между символами */
    }
    QLineEdit:focus {
        border: 2px solid #9B4DCA;
    }
"""

nickname_style_sheet = """
    QLineEdit {
        height: 30px;             /* Увеличиваем высоту поля ввода */
        padding: 10px;            /* Добавляем отступы внутри поля */
        border-radius: 10px;       /* Скругляем углы */
        border: 4px solid #121212; /* Цвет и толщина границы по умолчанию */
        background-color: #333333; /* Цвет фона */
        color: #E8E8E8;           /* Цвет текста */
    }

    QLineEdit:focus {
        border: 2px solid #9B4DCA;   /* Цвет рамки при фокусе (фиолетовый) */
    }
"""