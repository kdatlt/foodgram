from django.contrib.auth.models import AbstractUser
from django.db import models

from users.const import MAX_BIO_LENGHT, MAX_ROLE_LENGTH


class MyUser(AbstractUser):
    """Кастомная модель пользователя."""
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
