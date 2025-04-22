from django.shortcuts import render
from rest_framework import filters, permissions, status, viewsets
from rest_framework.views import APIView

from recipes.models import Ingredient, Tag, User


class SignUpAPIView(APIView):
    """Обрабатывает POST запрос на регистрацию нового пользователя."""

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')

        user = User.objects.filter(username=username, email=email).first()

        if user:
            confirmation_code = default_token_generator.make_token(user)
            send_confirmation_code(confirmation_code, user.email)
            return Response(
                {'email': email, 'username': username},
                status=status.HTTP_200_OK,
            )

        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        confirmation_code = default_token_generator.make_token(user)
        send_confirmation_code(confirmation_code, user.email)
        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK,
        )


class TokenAccessObtainView(APIView):
    """Обрабатывает POST запрос на получения токена."""

    def post(self, request):
        serializer = TokenAccessObtainSerializer(
            data=request.data, context=request.data
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        access_token = AccessToken.for_user(user)

        return Response(
            {'token': str(access_token)}, status=status.HTTP_200_OK
        )


class UserViewSet(ModelViewSet):
    """Обрабатывает запросы к данным пользователей."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminOrSuperuser,)
    filter_backends = (SearchFilter,)
    search_fields = ('username',)
    lookup_field = 'username'
    http_method_names = (
        'get',
        'post',
        'patch',
        'delete',
    )

    def get_permissions(self):
        if 'me' in self.request.path:
            return [
                IsAuthenticated(),
            ]
        return super().get_permissions()

    @action(methods=['get'], detail=False, url_name='me')
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @me.mapping.patch
    def me_update(self, request):
        serializer = UserSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.pop('role', None)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели Ingredient."""
    queryset = Ingredient.objects.all()
    # serializer_class = IngredientSerializer
    # permission_classes = (permissions.AllowAny,)
    # filter_backends = (filters.SearchFilter,)
    # search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели Tag."""
    queryset = Tag.objects.all()
    # serializer_class = TagSerializer
    # permission_classes = (permissions.AllowAny,)
