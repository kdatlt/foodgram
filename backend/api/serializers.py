from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer, UserCreateSerializer
from django.core.files.base import ContentFile
import base64

from recipes.models import Ingredient, Recipe, Tag


User = get_user_model()


class Base64ImageField(serializers.Field):
    def to_internal_value(self, data):
        # Проверяем, что данные не пустые
        if not data:
            return None

        # Проверяем, что данные являются строкой base64
        if isinstance(data, str):
            try:
                # Декодируем строку base64 в байты
                decoded_file = base64.b64decode(data)
            except (TypeError, ValueError, UnicodeDecodeError) as e:
                raise serializers.ValidationError("Некорректные данные base64")

            # Создаём объект файла из декодированных данных
            file_object = ContentFile(decoded_file, name='uploaded_image.jpg')

            return file_object
        else:
            raise serializers.ValidationError(
                "Данные должны быть строкой base64")


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'unit_of_measure')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = '__all__'


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password'
        )

    def validate(self, data):
        if data['email'] == data['username']:
            raise serializers.ValidationError(
                'Имя пользователя не должно совпадать '
                'с адресом электронной почты!'
            )
        return data
