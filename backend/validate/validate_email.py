from email_validator import validate_email, EmailNotValidError

def validate_email_address(email: str) -> bool:
    try:
        valid = validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False
