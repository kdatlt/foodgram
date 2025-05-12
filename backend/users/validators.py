from api.constants import INVALID_USERNAME
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

USERNAME_VALIDATOR = RegexValidator(
    r'^[\w.@+-]+\Z', 'Имя пользователя содержит недопустимые символы.')


def validate_username(value):
    if value.lower() == INVALID_USERNAME:
        raise ValidationError(
            f'Недопустимое имя пользователя - {INVALID_USERNAME}.')
