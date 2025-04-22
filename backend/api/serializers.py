from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer, UserCreateSerializer


from recipes.models import Tag

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


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
