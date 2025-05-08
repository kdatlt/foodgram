from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import REGEX_USERNAME, validate_username


class MyUser(AbstractUser):
    """Модель пользователя."""
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=False,
        validators=(REGEX_USERNAME, validate_username),
    )
    email = models.EmailField(max_length=254, unique=True, blank=False)
    first_name = models.CharField('Имя', max_length=150, blank=False)
    last_name = models.CharField('Фамилия', max_length=150, blank=False)
    avatar = models.ImageField(
        'Аватар',
        upload_to='images/avatar/',
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.username
