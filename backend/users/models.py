from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import REGEX_USERNAME, validate_username


class User(AbstractUser):
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


class Subscription(models.Model):
    """Модель подписки."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribed_to',
        verbose_name='Пользователь'
    )
    subscribed_to = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Подписан на'
    )

    class Meta:
        verbose_name = 'подписки'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscribed_to'],
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.subscribed_to}'
