from django.urls import path
from .views import OrderReturnListView, OrderReturnDetailViev, OrderReturnUpdateView, OrderReturnDeleteView, OrderReturnItemListView, OrderReturnItemDetailViev, OrderReturnItemUpdateView, OrderReturnItemDeleteView

app_name = 'order_returns'

urlpatterns = [
    path('order-returns/', OrderReturnListView.as_view(), name='order_returns_list'),
    path('order-returns/<str:pk>/', OrderReturnDetailViev.as_view(), name='order_return_detail'),
    path('order-returns/<str:pk>/update/', OrderReturnUpdateView.as_view(), name='order_return_update'),
    path('order-returns/<str:pk>/delete/', OrderReturnDeleteView.as_view(), name='order_return_delete'),
    path('order-return-items/', OrderReturnItemListView.as_view(), name='order_return_items_list'),
    path('order-return-items/<str:pk>/', OrderReturnItemDetailViev.as_view(), name='order_return_item_detail'),
    path('order-return-items/<str:pk>/update/', OrderReturnItemUpdateView.as_view(), name='order_return_item_update'),
    path('order-return-items/<str:pk>/delete/', OrderReturnItemDeleteView.as_view(), name='order_return_item_delete'),
]
