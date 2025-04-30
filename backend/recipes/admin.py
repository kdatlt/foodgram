from django.contrib.admin import ModelAdmin, register

from .models import (
    Ingredient, Tag, IngredientRecipe, TagRecipe, Recipe,
    Follow, Favorite)


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = (
        'pk', 'name', 'author', 'pub_date', 'get_favorites', 'get_tags')
    list_filter = ('author', 'name', 'tags')
    search_fields = ('name',)

    def get_favorites(self, obj: Recipe) -> int:
        return obj.favorites.count()

    get_favorites.short_description = (
        'Количество добавлений рецепта в избранное'
    )

    def get_tags(self, obj):
        return '\n'.join(obj.tags.values_list('name', flat=True))

    get_tags.short_description = 'Тег или список тегов'


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('pk', 'name', 'slug')


@register(IngredientRecipe)
class IngredientInRecipe(ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')

"""
@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
"""

@register(Follow)
class FollowAdmin(ModelAdmin):
    list_display = ('pk', 'user', 'author')
    search_fields = ('user', 'author')
    list_filter = ('user', 'author')


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('pk', 'user', 'recipe')


@register(TagRecipe)
class TagRecipeAdmin(ModelAdmin):
    list_display = ('pk', 'tag', 'recipe')
