from django.http import HttpResponse
from django.shortcuts import render
from djoser.views import UserViewSet
from rest_framework import filters, permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny
from django.db.models import Sum

from recipes.models import (
    Favorite, Ingredient, Recipe, Tag, User, ShoppingCart, IngredientRecipe)

from .permissions import IsAuthorOrReadOnly
from .pagination import CustomPagination
from .serializers import (CustomUserSerializer, FavoritesSerializer,
                          IngredientSerializer, RecipeSerializer,
                          TagSerializer, FavoritesSerializer,
                          ShoppingCartSerializer, RecipeCreateSerializer)

from .utils import get_short_link


class CustomUserViewSet(UserViewSet):
    """Вьюсет для модели User."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(permissions.IsAuthenticated,),
        url_path='me'
    )
    def me(self, request):
        """Получение информации о текущем пользователе."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        if self.action == 'subscriptions':
            queryset = User.objects.filter(
                subscription__user=self.request.user
            )
            return queryset
        return super().get_queryset()

    def get_serializer_class(self):
        if self.action == 'avatar':
            return AvatarSerializer
        if self.action == 'subscriptions':
            return UserWithRecipesSerializer
        if self.action == 'subscribe':
            return SubscriptionSerializer
        return super().get_serializer_class()


    @action(
        detail=True,
        methods=['put', ],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def avatar(self, request, **kwargs):
        """Добавление аватара."""
        serializer = self.get_serializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request, **kwargs):
        """Удаление аватара."""
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get', ],
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Список подписок текущего пользователя."""
        page = self.paginate_queryset(self.get_queryset())
        serializer = self.get_serializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscribe(self, request, **kwargs):
        """Подписка на пользователя."""
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request, 'subscribed_to': self.get_object()}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, subscribed_to=self.get_object())
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, **kwargs):
        """Отписка от пользователя."""
        try:
            subscription = Subscription.objects.get(
                user=request.user, subscribed_to=self.get_object()
            )
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели Ingredient."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели Tag."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Recipe."""
    queryset = Recipe.objects.all()

    serializer_class = RecipeSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    # filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            short_link=get_short_link(Recipe)
        )

    def get_serializer_class(self):
        if self.action == 'favorite':
            return FavoritesSerializer
        if self.action == 'shopping_cart':
            return ShoppingCartSerializer
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return RecipeCreateSerializer

    @action(
        detail=True, methods=['get'],
        permission_classes=(AllowAny,), url_path='get-link')
    def get_link(self, request, **kwargs):
        """Получение короткой ссылки на рецепт."""
        try:
            recipe = self.get_object()
            short_link = recipe.short_link
        except Exception as e:
            return Response(
                {'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        # Формирование полного URL для короткой ссылки
        base_url = request.build_absolute_uri('/')
        short_url = f"{base_url}s/{short_link}"

        return Response({'short-link': short_url}, status=status.HTTP_200_OK)

    def add_to_favorites(self, request, model):
        """Добавление рецепта в 'Избранное' или в 'Список покупок'."""
        try:
            recipe = self.get_object()
            serializer = self.get_serializer(
                data=request.data,
                context={'request': request, 'recipe': recipe, 'model': model})
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user, recipe=recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception:
            return Response(
                {'error': 'Произошла ошибка при добавлении рецепта'},
                status=status.HTTP_400_BAD_REQUEST)

    def delete_from_favorites(self, request, model):
        """Удаление рецепта из 'Избранного' или 'Списка покупок'."""
        try:
            obj = model.objects.get(
                user=request.user, recipe=self.get_object())
        except model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(permissions.IsAuthenticated,),
    )
    def favorite(self, request, **kwargs):
        return self.add_to_favorites(request=request, model=Favorite)

    @favorite.mapping.delete
    def delete_favorite(self, request, **kwargs):
        return self.delete_from_favorites(request=request, model=Favorite)

    @action(
        detail=True, methods=['post'],
        permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, **kwargs):
        return self.add_to_favorites(request=request, model=ShoppingCart)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, **kwargs):
        return self.delete_from_favorites(request=request, model=ShoppingCart)

    @action(
        detail=False,
        methods=['get', ],
        permission_classes=(permissions.IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Скачивание 'Списка покупок'."""
        indredients = IngredientRecipe.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount_sum=Sum('amount'))
        shopping_cart = ''
        for ingredient in indredients:
            name = ingredient['ingredient__name']
            measurement_unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['amount_sum']
            shopping_cart += f'{name} - {amount} {measurement_unit}\n'
        return HttpResponse(shopping_cart, content_type='text/plain')


class FavoriteViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Favorite."""
    queryset = Favorite.objects.all()
    serializer_class = FavoritesSerializer
    permission_classes = (permissions.AllowAny,)
