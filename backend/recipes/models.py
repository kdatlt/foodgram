from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from users.models import User


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField('Название', max_length=128, blank=False)
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=64,
        blank=False
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(
        'Название',
        max_length=32,
        unique=True,
        blank=False
    )
    slug = models.SlugField(
        max_length=32,
        unique=True,
        blank=False,
        validators=(RegexValidator(r'^[-a-zA-Z0-9_]+$'),),
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = models.CharField('Название', max_length=256, blank=False)
    image = models.ImageField(
        'Фото блюда',
        upload_to='images/recipes/',
        blank=False
    )
    text = models.TextField('Описание рецепта', blank=False)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        blank=False,
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
        blank=False,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления, мин',
        blank=False,
        validators=(MinValueValidator(1),)
    )
    short_link = models.CharField(
        'Короткая ссылка',
        max_length=5,
        unique=True,
        blank=True
    )

    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """Промежуточная модель для Ingredient и Recipe."""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients_in_recipe',
        verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        blank=False,
        validators=(MinValueValidator(1),)
    )

    class Meta:
        verbose_name = 'ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredientrecipe'
            )
        ]

    def __str__(self):
        return f'Ингредиент: {self.ingredient} в рецепте: {self.recipe}'


class TagRecipe(models.Model):
    """Промежуточная модель для Tag и Recipe."""
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, verbose_name='Тег')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'теги в рецепте'
        verbose_name_plural = 'Теги в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'recipe'],
                name='unique_tagrecipe'
            )
        ]

    def __str__(self):
        return f'Рецепт: {self.recipe} с тегом: {self.tag}'


class ShoppingCart(models.Model):
    """Модель списка покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shoppingcart'
            )
        ]

    def __str__(self):
        return f'Рецепт: {self.recipe} в корзине у {self.user}'


class Favorite(models.Model):
    """Модель избранного."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'Рецепт: {self.recipe} в избранном у {self.user}'

