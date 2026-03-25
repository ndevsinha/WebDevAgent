from django.urls import path
from .views import EvaluateEquationView

urlpatterns = [
    path('evaluate/', EvaluateEquationView.as_view(), name='evaluate-equation'),
]
