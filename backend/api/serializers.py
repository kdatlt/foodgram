from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer, UserCreateSerializer
from django.core.files.base import ContentFile
import base64

from recipes.models import Ingredient, Recipe, Tag, Follow, TagRecipe, IngredientRecipe


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
            except (TypeError, ValueError, UnicodeDecodeError):
                raise serializers.ValidationError('Некорректные данные base64')

            # Создаём объект файла из декодированных данных
            file_object = ContentFile(decoded_file, name='uploaded_image.jpg')

            return file_object
        else:
            raise serializers.ValidationError(
                'Данные должны быть строкой base64')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""
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


class CustomUserSerializer(UserCreateSerializer):
    """Сериализатор для модели User."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Мета-параметры сериализатора"""

        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        """Метод проверки подписки"""

        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели IngredientRecipe."""

    class Meta:
        model = IngredientRecipe
        fields = '__all__'


class TagRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели TagRecipe."""

    class Meta:
        model = TagRecipe
        fields = '__all__'


class FavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления в избранное по модели Recipe."""

    class Meta:
        """Мета-параметры сериализатора"""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
