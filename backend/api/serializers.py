import base64

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers

from recipes.models import (
    Favorite, Ingredient, IngredientRecipe,
    Recipe, ShoppingCart, Tag, TagRecipe
)
from users.models import Subscription, User


class Base64ImageField(serializers.ImageField):
    """Поле для кодирования изображения в base64."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CheckMixin(serializers.ModelSerializer):

    def checking_fields(self, model, obj):
        """Получает значения True или False для полей:
        is_subscribed, is_favorited, is_in_shopping_cart.
        """
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        if model == Subscription:
            return Subscription.objects.filter(
                user=request.user, subscribed_to=obj
            ).exists()
        return model.objects.filter(user=request.user, recipe=obj).exists()


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


class CustomUserSerializer(UserSerializer, CheckMixin):
    """Сериализатор для модели User."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        return self.checking_fields(model=Subscription, obj=obj)


class AvatarSerializer(CustomUserSerializer):
    """Сериализатор для модели User при PUT-запросе на добавление аватара."""

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data):
        if not data.get('avatar'):
            raise serializers.ValidationError('Аватар не добавлен!')
        return data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientForRecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для поля ingredients в RecipeCreateSerializer."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0!'
            )
        return value


class IngredientForRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для поля ingredients в RecipeReadSerializer."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeReadSerializer(CheckMixin):
    """Сериализатор для модели Recipe при GET-запросах."""

    tags = TagSerializer(many=True)
    author = CustomUserSerializer()
    ingredients = IngredientForRecipeReadSerializer(
        many=True, source='ingredients_in_recipe'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, obj):
        return self.checking_fields(model=Favorite, obj=obj)

    def get_is_in_shopping_cart(self, obj):
        return self.checking_fields(model=ShoppingCart, obj=obj)


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe при POST, PATCH, DELETE запросах."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, allow_empty=False
    )
    ingredients = IngredientForRecipeCreateSerializer(
        many=True, allow_empty=False
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'tags', 'author', 'ingredients', 'name',
            'image', 'text', 'cooking_time', 'short_link'
        )
        read_only_fields = ('author', 'short_link')

    def validate(self, data):
        if not self.initial_data.get('tags'):
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один тег!'
            )
        if not self.initial_data.get('ingredients'):
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один ингредиент!'
            )
        return data

    def validate_tags(self, value):
        for tag in value:
            if value.count(tag) > 1:
                raise serializers.ValidationError(
                    'Теги не должны повторяться!'
                )
        return value

    def validate_ingredients(self, value):
        ingredients_id = []
        for ingredient in value:
            id = ingredient['id']
            try:
                Ingredient.objects.get(id=id)
            except ObjectDoesNotExist:
                raise serializers.ValidationError(
                    f'Ингредиента с id={id} не существует!'
                )
            if id in ingredients_id:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться!'
                )
            ingredients_id.append(id)
        return value

    def create_tags(self, tags, recipe):
        for tag in tags:
            TagRecipe.objects.create(tag=tag, recipe=recipe)

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            current_ingredient = Ingredient.objects.get(pk=ingredient['id'])
            IngredientRecipe.objects.create(
                ingredient=current_ingredient,
                recipe=recipe,
                amount=ingredient['amount']
            )

    def get_tags(self, data):
        return data.pop('tags')

    def get_ingredients(self, data):
        return data.pop('ingredients')

    @transaction.atomic
    def create(self, validated_data):
        tags = self.get_tags(validated_data)
        ingredients = self.get_ingredients(validated_data)
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(ingredients, recipe)
        self.create_tags(tags, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        TagRecipe.objects.filter(recipe=instance).delete()
        self.create_tags(self.get_tags(validated_data), instance)

        IngredientRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients(self.get_ingredients(validated_data), instance)

        instance = super().update(instance, validated_data)
        instance.save()
        return instance

    def to_representation(self, instance):
        """Сериализация ответа на POST-запрос."""
        serializer = RecipeReadSerializer(instance)
        return serializer.data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe (укороченный вариант).

    Используется в FavoriteSerializer,
    ShoppingCartSerializer,
    UserWithRecipesSerializer.
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class FavoriteShoppingCartMixin(serializers.ModelSerializer):
    """Миксин для сериализаторов FavoriteSerializer, ShoppingCartSerializer."""

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
        serializer = ShortRecipeSerializer(instance.recipe)
        return serializer.data


class FavoriteSerializer(FavoriteShoppingCartMixin):
    """Сериализатор для модели Favorite."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)
        read_only_fields = ('user', 'recipe',)


class ShoppingCartSerializer(FavoriteShoppingCartMixin):
    """Сериализатор для модели ShoppingCart."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)
        read_only_fields = ('user', 'recipe',)


class UserWithRecipesSerializer(CustomUserSerializer):
    """Сериализатор для модели User с его рецептами."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source="recipes.count")

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = ShortRecipeSerializer(recipes, many=True)
        return serializer.data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Subscription."""

    class Meta:
        model = Subscription
        fields = ('user', 'subscribed_to',)
        read_only_fields = ('user', 'subscribed_to',)

    def validate(self, data):
        user = self.context.get('request').user
        subscribed_to = self.context.get('subscribed_to')
        if user == subscribed_to:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!'
            )
        if Subscription.objects.filter(
            user=user, subscribed_to=subscribed_to
        ).exists():
            raise serializers.ValidationError(
                f'Вы уже подписаны на {subscribed_to.username}!'
            )
        return data

    def to_representation(self, instance):
        serializer = UserWithRecipesSerializer(
            instance.subscribed_to,
            context=self.context
        )
        return serializer.data
