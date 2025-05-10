def validate_passwords(password, confirm_password):
    if password == confirm_password:
        if len(password) > 4:
            if " " not in password:
                return "Успешно!"
            else:
                return "Пароль должен быть без пробела."
        else:
            return "Пароль должен состоять как минимум из 5 символов."
    else:
        return "Пароли не совпадают."