import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import (Follow, Ingredient, IngredientRecipe, Recipe, Tag,
                            TagRecipe, ShoppingCart, Subscription, URL)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """
    Класс для декодирования изображений в формате base64.

    Принимает строку в формате
    'data:image/<тип изображения>;base64,<данные изображения в base64>'
    и преобразует её в объект ContentFile с соответствующим расширением файла.
    """

    def to_internal_value(self, data):
        """Метод преобразования картинки"""

        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='photo.' + ext)

        return super().to_internal_value(data)


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
        """Проверка подписки"""

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


class MinimalRecipeSerializer(serializers.ModelSerializer):
    """Универсальный сериализатор для модели Recipe."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class UserRecipesSerializer(CustomUserSerializer):
    """Сериализатор пользователя с рецептами."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source="recipes.count")

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        serializer = MinimalRecipeSerializer(recipes, many=True)
        return serializer.data


class FavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в избранное."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, data):
        user = self.context.get('request').user
        recipe = self.context.get('recipe')
        model = self.context.get('model')
        if model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Рецепт - {recipe.name} уже добавлен!'
            )
        return data

    def to_representation(self, instance):
        serializer = MinimalRecipeSerializer(instance.recipe)
        return serializer.data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ShoppingCart."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)
        read_only_fields = ('user', 'recipe',)

    def validate(self, data):
        user = self.context.get('request').user
        recipe = self.context.get('recipe')
        model = self.context.get('model')
        if model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Рецепт - {recipe.name} уже добавлен!'
            )
        return data

    def to_representation(self, instance):
        serializer = MinimalRecipeSerializer(instance.recipe)
        return serializer.data


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
    # author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        """Мета-параметры сериализатора"""

        model = Recipe
        fields = ('ingredients', 'tags', 'name',
                  'image', 'text', 'cooking_time')


class AvatarSerializer(CustomUserSerializer):
    """Сериализатор для добавление аватара."""

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data):
        if not data.get('avatar'):
            raise serializers.ValidationError('Аватар не добавлен.')
        return data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Subscription."""

    class Meta:
        model = Subscription
        fields = ('user', 'subscribed_to',)
        read_only_fields = ('user', 'subscribed_to',)

    def validate(self, data):
        user = self.context.get('request').user
        subscribed_to = self.context.get('subscribed_to')

        # Проверка на подписку на самого себя
        if user == subscribed_to:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!')

        # Проверка на наличие уже существующей подписки
        if self.is_already_subscribed(user, subscribed_to):
            raise serializers.ValidationError(
                f'Вы уже подписаны на {subscribed_to.username}!')
        return data

    def to_representation(self, instance):
        serializer = UserRecipesSerializer(
            instance.subscribed_to, context=self.context)
        return serializer.data


class URLSerializer(serializers.ModelSerializer):
    """Сериализатор для ссылок."""
    class Meta:
        model = URL
        fields = ['long_url']
