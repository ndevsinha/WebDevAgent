from django.contrib import admin
from django.urls import path
from api.views import calculate_points

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/calculate/', calculate_points, name='calculate_points'),
]
