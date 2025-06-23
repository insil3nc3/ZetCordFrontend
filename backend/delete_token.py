import json
import os

def clear_token_value():
    path = os.path.join(os.path.dirname(__file__), "../token.json")
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Удаляем ключ "token" или обнуляем его значение
        if "refresh_token" in data:
            data["refresh_token"]  = ""

        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        print("✅ Значение ключа 'refresh_token' успешно удалено.")
    except Exception as e:
        print(f"❌ Ошибка при очистке токена: {e}")
