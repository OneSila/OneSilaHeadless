from django.urls import path
from .views import VatRateListView, VatRateDetailViev, VatRateUpdateView, VatRateDeleteView

app_name = 'taxes'

urlpatterns = [
    path('taxes/vat-rates/', VatRateListView.as_view(), name='vat_rates_list'),
    path('taxes/vat-rates/<str:pk>/', VatRateDetailViev.as_view(), name='vat_rates_detail'),
    path('taxes/vat-rates/<str:pk>/update/', VatRateUpdateView.as_view(), name='vat_rates_update'),
    path('taxes/vat-rates/<str:pk>/delete/', VatRateDeleteView.as_view(), name='vat_rates_delete'),
]
