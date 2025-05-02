import uuid
from django.shortcuts import get_object_or_404, redirect

from recipes.models import Recipe


def get_short_link(model):
    while True:
        short_link = str(uuid.uuid4())[:5]
        if not model.objects.filter(short_link=short_link).exists():
            return short_link


def recipe_redirection(request, short_link):
    # Получение рецепта по короткой ссылке, если не найден - автоматически возвращаем 404
    recipe = get_object_or_404(Recipe, short_link=short_link)
    recipe_id = recipe.id

    # Формирование полного URL для перенаправления
    redirect_url = request.build_absolute_uri('/') + f'recipes/{recipe_id}/'

    return redirect(redirect_url)
