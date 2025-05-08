from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


USERNAME_VALIDATOR = RegexValidator(
    r'^[\w.@+-]+\Z', 'Имя пользователя содержит недопустимые символы.')


def validate_username(value):
    if value.lower() == 'me':
        raise ValidationError(
            'Недопустимое имя пользователя - me.',)
