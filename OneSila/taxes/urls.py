from django.urls import path
from .views import TaxListView, TaxDetailViev, TaxUpdateView, TaxDeleteView

app_name = 'taxes'

urlpatterns = [
    path('taxes/', TaxListView.as_view(), name='taxes_list'),
    path('taxes/<str:pk>/', TaxDetailViev.as_view(), name='tax_detail'),
    path('taxes/<str:pk>/update/', TaxUpdateView.as_view(), name='tax_update'),
    path('taxes/<str:pk>/delete/', TaxDeleteView.as_view(), name='tax_delete'),
]
