from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(
        max_length=150, blank=False, db_index=True, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=50, blank=False, verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.unit_of_measure}'


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(
        max_length=50, unique=True, blank=False, verbose_name='Название')
    slug = models.SlugField(
        max_length=50, unique=True, blank=False,
        validators=[RegexValidator(r'^[-a-zA-Z0-9_]+$')])

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientRecipe', blank=False,
        verbose_name='Ингредиенты')
    tags = models.ManyToManyField(
        Tag, through='TagRecipe', blank=False, verbose_name='Тег')
    image = models.ImageField(
        blank=False, upload_to='images/recipes/', verbose_name='Фото')
    name = models.CharField(
        max_length=256, blank=False, verbose_name='Название')
    text = models.TextField(blank=False, verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        blank=False, validators=[MinValueValidator(1)],
        verbose_name='Время приготовления, мин')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes',
        verbose_name='Автор')
    short_link = models.CharField(
        max_length=7, unique=True, blank=True, verbose_name='Короткая ссылка')
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации')

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """Промежуточная модель для Ingredient и Recipe."""
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='Ингредиент')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='ingredients_in_recipe',
        verbose_name='Рецепт')
    amount = models.PositiveSmallIntegerField(
        blank=False, validators=[MinValueValidator(1)],
        verbose_name='Количество')

    class Meta:
        verbose_name = 'ингредиенты рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
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
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, verbose_name='Тег')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт')

    class Meta:
        verbose_name = 'тег рецепта'
        verbose_name_plural = 'Теги рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'recipe'],
                name='unique_tagrecipe'
            )
        ]

    def __str__(self):
        return f'Рецепт: {self.recipe} с тегом: {self.tag}'


class Follow(models.Model):
    """ Модель для создания подписок на автора"""

    author = models.ForeignKey(
        User, related_name='follow', on_delete=models.CASCADE,
        verbose_name='Автор')
    user = models.ForeignKey(
        User, related_name='follower', on_delete=models.CASCADE,
        verbose_name='Подписчик')

    class Meta:
        """Мета-параметры модели"""

        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_follow'
            )
        ]

    def __str__(self):
        """Метод строкового представления модели."""

        return f'{self.user} {self.author}'
