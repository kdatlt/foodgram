from django.contrib.admin import ModelAdmin, register

from .models import (
    Favorite, Ingredient, IngredientRecipe,
    Recipe, ShoppingCart, Tag, TagRecipe, Subscription)


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name',)


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@register(IngredientRecipe)
class IngredientRecipeAdmin(ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = (
        'pk', 'name', 'author', 'pub_date', 'get_favorites', 'get_tags')
    list_filter = ('author', 'name', 'tags')
    search_fields = ('name',)

    def get_favorites(self, obj: Recipe):
        return obj.favorites.count()

    get_favorites.short_description = (
        'Количество добавлений рецепта в избранное'
    )

    def get_tags(self, obj):
        return '\n'.join(obj.tags.values_list('name', flat=True))

    get_tags.short_description = 'Тег или список тегов'


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name',)


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


@register(TagRecipe)
class TagRecipeAdmin(ModelAdmin):
    list_display = ('tag', 'recipe')
    search_fields = ('tag__name', 'recipe__name')


@register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = ('user', 'subscribed_to')
    search_fields = ('user__username', 'subscribed_to__username')
