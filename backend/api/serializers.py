import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import (Follow, Ingredient, IngredientRecipe, Recipe, Tag,
                            TagRecipe, IngredientRecipe)

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


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}

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

    ingredient = IngredientSerializer(read_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('ingredient', 'amount')


class TagRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели TagRecipe."""

    tag = TagSerializer(read_only=True)

    class Meta:
        model = TagRecipe
        fields = ('tag',)


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""

    ingredients = IngredientRecipeSerializer(
        source='ingredients_in_recipe', many=True)
    tags = TagRecipeSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'cooking_time',
            'image', 'ingredients', 'tags')

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients_in_recipe')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            IngredientRecipe.objects.create(recipe=recipe, **ingredient_data)
        for tag_data in tags_data:
            TagRecipe.objects.create(recipe=recipe, **tag_data)
        return recipe


class FavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления в избранное по модели Recipe."""

    class Meta:
        """Мета-параметры сериализатора"""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientCreatesRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецептах"""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    @staticmethod
    def validate_amount(value):
        """Метод валидации количества"""

        if value < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0!'
            )
        return value

    class Meta:
        """Мета-параметры сериализатора"""

        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов"""

    ingredients = IngredientCreatesRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    image = Base64ImageField()
    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        """Мета-параметры сериализатора"""

        model = Recipe
        fields = ('ingredients', 'tags', 'name',
                  'image', 'text', 'cooking_time')
