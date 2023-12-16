from django.urls import path
from .views import UnitListView, UnitDetailViev, UnitUpdateView, UnitDeleteView

app_name = 'units'

urlpatterns = [
    path('units/', UnitListView.as_view(), name='units_list'),
    path('units/<str:pk>/', UnitDetailViev.as_view(), name='unit_detail'),
    path('units/<str:pk>/update/', UnitUpdateView.as_view(), name='unit_update'),
    path('units/<str:pk>/delete/', UnitDeleteView.as_view(), name='unit_delete'),
]
