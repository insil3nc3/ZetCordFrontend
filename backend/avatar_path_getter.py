import os
def find_image_path_by_number(folder_path: str, number: int) -> str | None:
    for ext in ['.png', '.jpg', '.jpeg', '.webp']:  # можно добавить другие
        file_path = os.path.join(folder_path, f"{number}{ext}")
        if os.path.isfile(file_path):
            print(file_path)
            return file_path
    return None  # если не найден