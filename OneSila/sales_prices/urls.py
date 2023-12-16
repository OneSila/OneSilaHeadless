from django.urls import path
from .views import SalesPriceListView, SalesPriceDetailViev, SalesPriceUpdateView, SalesPriceDeleteView, SalesPriceListListView, SalesPriceListDetailViev, SalesPriceListUpdateView, SalesPriceListDeleteView, SalesPriceListItemListView, SalesPriceListItemDetailViev, SalesPriceListItemUpdateView, SalesPriceListItemDeleteView

app_name = 'sales_prices'

urlpatterns = [
    path('sales-prices/', SalesPriceListView.as_view(), name='sales_prices_list'),
    path('sales-prices/<str:pk>/', SalesPriceDetailViev.as_view(), name='sales_price_detail'),
    path('sales-prices/<str:pk>/update/', SalesPriceUpdateView.as_view(), name='sales_price_update'),
    path('sales-prices/<str:pk>/delete/', SalesPriceDeleteView.as_view(), name='sales_price_delete'),
    path('sales-price-lists/', SalesPriceListListView.as_view(), name='sales_price_lists_list'),
    path('sales-price-lists/<str:pk>/', SalesPriceListDetailViev.as_view(), name='sales_price_list_detail'),
    path('sales-price-lists/<str:pk>/update/', SalesPriceListUpdateView.as_view(), name='sales_price_list_update'),
    path('sales-price-lists/<str:pk>/delete/', SalesPriceListDeleteView.as_view(), name='sales_price_list_delete'),
    path('sales-price-list-items/', SalesPriceListItemListView.as_view(), name='sales_price_list_items_list'),
    path('sales-price-list-items/<str:pk>/', SalesPriceListItemDetailViev.as_view(), name='sales_price_list_item_detail'),
    path('sales-price-list-items/<str:pk>/update/', SalesPriceListItemUpdateView.as_view(), name='sales_price_list_item_update'),
    path('sales-price-list-items/<str:pk>/delete/', SalesPriceListItemDeleteView.as_view(), name='sales_price_list_item_delete'),
]
