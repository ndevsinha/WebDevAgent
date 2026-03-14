from django.urls import path
from .views import CurveListView, CurveDataView

urlpatterns = [
    path('curves/', CurveListView.as_view(), name='curve-list'),
    path('curves/<str:curve_id>/', CurveDataView.as_view(), name='curve-data'),
]