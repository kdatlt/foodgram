from django.contrib import admin
from django.urls import include, path
from api import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
    path(
        's/<str:shorturl>/', views.redirect_to_long_url,
        name='redirect_to_long_url'),

]
