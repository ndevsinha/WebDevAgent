from django.urls import path
from .views import calculate_plot

urlpatterns = [
    path('plot/', calculate_plot, name='calculate_plot'),
]
