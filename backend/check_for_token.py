import os
import json

def check_for_token_existing():
    path = "token.json"
    if not os.path.isfile(path):

        with open(path, "w", encoding="utf-8") as file:
            json.dump({"refresh_token": ""}, file, ensure_ascii=False, indent=1)
        print("файла с токеном нет")
        return -1

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
            if data.get("refresh_token"):
                print("файл с тоекном есть и в нем есть токен")
                return 1
    except json.JSONDecodeError:
        pass
    print("файл есть но токена нет")
    return 0  # файл есть, но refresh_token пустой или некорректный
