import re

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


def validate_username(value):
    if not re.match(r'^[\w.@+-]+\Z', value):
        raise ValidationError(
            'Имя пользователя содержит недопустимые символы.')


class MyUser(AbstractUser):
    """Кастомная модель пользователя."""
    email = models.EmailField(max_length=254, unique=True, blank=False)
    username = models.CharField(
        max_length=150, unique=True, blank=False,
        validators=[validate_username],)
    first_name = models.CharField(
        max_length=150, blank=False, verbose_name='Имя')
    last_name = models.CharField(
        max_length=150, blank=False, verbose_name='Фамилия')
    avatar = models.ImageField(
        upload_to='images/avatar/', blank=True, verbose_name='Аватар')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.username
