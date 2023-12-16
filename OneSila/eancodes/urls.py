from django.urls import path
from .views import EanCodeListView, EanCodeDetailViev, EanCodeUpdateView, EanCodeDeleteView


app_name = 'eancodes'

urlpatterns = [
    path('ean-codes/', EanCodeListView.as_view(), name='ean_codes_list'),
    path('ean-codes/<str:pk>/', EanCodeDetailViev.as_view(), name='ean_code_detail'),
    path('ean-codes/<str:pk>/update/', EanCodeUpdateView.as_view(), name='ean_code_update'),
    path('ean-codes/<str:pk>/delete/', EanCodeDeleteView.as_view(), name='ean_code_delete'),
]
