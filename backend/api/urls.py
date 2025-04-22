from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import UserViewSet, IngredientViewSet, RecipeViewSet, TagViewSet

router = DefaultRouter()

router.register(r'ingredients', IngredientViewSet)
router.register(r'tags', TagViewSet)
router.register(r'recipes', RecipeViewSet)
# router.register(r'users', CustomUserViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
