import backend.patch_av_error
import sys
import asyncio
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from api.auth import check_refresh_token_expired
from api.profile_actions import get_current_user
from api.private_chat import create_chat
from backend.audio_manager import AudioManager
from backend.check_for_token import check_for_token_existing

from screens.login_screen.login_screen import LoginWindow
from screens.main_screen.main_screen import MainWindow

import os
import av.logging
av.logging.set_level(av.logging.PANIC)

os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ["LANG"] = "en_US.UTF-8"
window = None
audio = AudioManager()
async def main():
    global window
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)

    asyncio.set_event_loop(loop)

    loop.create_task(main())

    with loop:
        loop.run_forever()
