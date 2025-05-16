from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin as Admin

from .models import User


@register(User)
class UserAdmin(Admin):
    list_display = ('pk', 'username', 'email', 'first_name', 'last_name',
                    'password', 'get_number_of_recipes')
    list_filter = ('username', 'email')
    search_fields = ('email', 'username')
