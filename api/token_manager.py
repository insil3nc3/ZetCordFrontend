import json
import os.path

import keyring  # пока не используется, но пригодится
from typing import Optional

class TokenManager:
    SERVICE_NAME = "ZETCORD"

    def __init__(self):
        self.access_token: Optional[str] = None

    def set_access_token(self, token: str):
        self.access_token = token

    def get_access_token(self) -> Optional[str]:
        return self.access_token

    def clear_access_token(self):
        self.access_token = None

    def set_refresh_token(self, token: str):
        data = {"refresh_token": token}
        with open("token.json", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=1)

    def get_refresh_token(self) -> Optional[str]:
        try:
            with open("token.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                return data.get("refresh_token")
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def clear_refresh_token(self):
        try:
            with open("token.json", "w", encoding="utf-8") as file:
                json.dump({"refresh_token": None}, file, ensure_ascii=False, indent=1)
        except Exception as e:
            print("Ошибка при очистке refresh токена:", e)

    def clear_all_tokens(self):
        self.clear_access_token()
        self.clear_refresh_token()

