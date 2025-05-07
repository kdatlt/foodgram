from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from api.utils import recipe_redirection


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:short_link>', recipe_redirection),
]
