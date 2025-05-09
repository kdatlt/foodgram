from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    """Модель для ингредиента."""
    name = models.CharField(
        max_length=128, blank=False, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=64, blank=False, verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    """Модель для тега."""
    name = models.CharField(
        max_length=32, unique=True, blank=False, verbose_name='Название')
    slug = models.SlugField(
        max_length=32, unique=True, blank=False,
        validators=(RegexValidator(r'^[-a-zA-Z0-9_]+$'),))

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель для рецепта."""
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes',
        verbose_name='Автор рецепта')
    name = models.CharField(
        max_length=256, blank=False, verbose_name='Название')
    image = models.ImageField(
        upload_to='images/recipes/', blank=False, verbose_name='Фото')
    text = models.TextField(blank=False, verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientRecipe', blank=False,
        verbose_name='Ингредиенты')
    tags = models.ManyToManyField(
        Tag, through='TagRecipe', blank=False, verbose_name='Теги')
    cooking_time = models.PositiveSmallIntegerField(
        blank=False, validators=(MinValueValidator(1),),
        verbose_name='Время приготовления')
    short_link = models.CharField(
        max_length=5, unique=True, blank=True, verbose_name='Короткая ссылка')
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации')

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """Промежуточная модель."""
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='Ингредиент')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='ingredients_in_recipe', verbose_name='Рецепт')
    amount = models.PositiveSmallIntegerField(
        blank=False, validators=(MinValueValidator(1),),
        verbose_name='Количество')

    class Meta:
        verbose_name = 'ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredientrecipe')]

    def __str__(self):
        return f'Ингредиент: {self.ingredient} в рецепте: {self.recipe}'


class TagRecipe(models.Model):
    """Промежуточная модель."""
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, verbose_name='Тег')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт')

    class Meta:
        verbose_name = 'теги в рецепте'
        verbose_name_plural = 'Теги в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'recipe'],
                name='unique_tagrecipe')]

    def __str__(self):
        return f'Рецепт: {self.recipe} с тегом: {self.tag}'


class ShoppingCart(models.Model):
    """Модель для списка покупок."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='shopping_cart',
        verbose_name='Рецепт')

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shoppingcart')]

    def __str__(self):
        return f'Рецепт: {self.recipe} в списке покупок {self.user}'


class Favorite(models.Model):
    """Модель для избранного."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorite',
        verbose_name='Рецепт')

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite')]

    def __str__(self):
        return f'Рецепт: {self.recipe} в избранном у {self.user}'


class Subscription(models.Model):
    """Модель для подписки."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscribed_to',
        verbose_name='Пользователь')
    subscribed_to = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Подписан на')

    class Meta:
        verbose_name = 'подписки'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscribed_to'],
                name='unique_subscription')]

    def __str__(self):
        return f'{self.user} подписан на {self.subscribed_to}'
