import os
import json

def check_for_token_existing():
    path = "token.json"
    if not os.path.isfile(path):

        with open(path, "w", encoding="utf-8") as file:
            json.dump({"refresh_token": ""}, file, ensure_ascii=False, indent=1)
        return -1

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
            if data.get("refresh_token"):
                return 1
    except json.JSONDecodeError:
        pass

    return 0  # файл есть, но refresh_token пустой или некорректный
