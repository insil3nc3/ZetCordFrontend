import backend.custom_opus
import backend.patch_av_error
import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop, asyncClose, asyncSlot
from backend.audio_manager import AudioManager
from screens.main_screen.main_screen import MainWindow
from screens.login_screen.login_screen import LoginWindow
from api.auth import check_refresh_token_expired
from backend.check_for_token import check_for_token_existing
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


async def async_main():
    try:
        # Инициализация аудио
        audio = AudioManager()
        logger.info("Audio manager initialized")

        # Проверка токена
        token_exist = check_for_token_existing()

        if token_exist == 1:
            refresh_result = await check_refresh_token_expired()
            if "request error" in refresh_result:
                window = LoginWindow("Ошибка с токеном, войдите заново", audio=audio)
            else:
                window = MainWindow(audio)
        else:
            window = LoginWindow(audio=audio)

        window.show()
        logger.info("Main window shown")

        # Ждем закрытия окна
        while getattr(window, 'isVisible', lambda: True)():
            await asyncio.sleep(0.1)

    except Exception as e:
        logger.error(f"Fatal error in async_main: {e}", exc_info=True)
        raise


def main():
    app = QApplication(sys.argv)

    try:
        # Настройка asyncio event loop
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)

        # Создаем и запускаем асинхронную часть
        main_task = loop.create_task(async_main())

        # Обработка завершения
        main_task.add_done_callback(
            lambda t: t.exception() and app.exit(1)
        )

        # Запуск основного цикла
        with loop:
            sys.exit(loop.run_forever())

    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()