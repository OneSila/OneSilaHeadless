from django.urls import path
from .views import CurrencyListView, CurrencyDetailViev, CurrencyUpdateView, CurrencyDeleteView


app_name = 'currencies'

urlpatterns = [
    path('currencies/', CurrencyListView.as_view(), name='currencies_list'),
    path('currencies/<str:pk>/', CurrencyDetailViev.as_view(), name='currency_detail'),
    path('currencies/<str:pk>/update/', CurrencyUpdateView.as_view(), name='currency_update'),
    path('currencies/<str:pk>/delete/', CurrencyDeleteView.as_view(), name='currency_delete'),
]
