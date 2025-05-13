from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin

from .models import ProjectUser


@register(ProjectUser)
class ProjectUserAdmin(UserAdmin):
    list_display = ('pk', 'username', 'email', 'first_name', 'last_name',
                    'password')
    list_filter = ('username', 'email')
    search_fields = ('email', 'username')
