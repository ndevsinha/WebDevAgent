from django.urls import path
from . import views

urlpatterns = [
    path('calculate/', views.calculate_points, name='calculate_points'),
]
