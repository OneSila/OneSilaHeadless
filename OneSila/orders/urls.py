from django.urls import path
from .views import OrderListView, OrderDetailViev, OrderUpdateView, OrderDeleteView, \
    OrderItemListView, OrderItemDetailViev, OrderItemUpdateView, OrderItemDeleteView, \
    OrderNoteListView, OrderNoteDetailViev, OrderNoteUpdateView, OrderNoteDeleteView, \
    OrderConfirmationFileViev

app_name = 'orders'

urlpatterns = [
    path('orders/', OrderListView.as_view(), name='orders_list'),
    path('orders/<str:pk>/', OrderDetailViev.as_view(), name='order_detail'),
    path('orders/<str:pk>/confirmation/', OrderConfirmationFileViev.as_view(), name='order_confirmation'),
    path('orders/<str:pk>/update/', OrderUpdateView.as_view(), name='order_update'),
    path('orders/<str:pk>/delete/', OrderDeleteView.as_view(), name='order_delete'),
    path('order-items/', OrderItemListView.as_view(), name='order_items_list'),
    path('order-items/<str:pk>/', OrderItemDetailViev.as_view(), name='order_item_detail'),
    path('order-items/<str:pk>/update/', OrderItemUpdateView.as_view(), name='order_item_update'),
    path('order-items/<str:pk>/delete/', OrderItemDeleteView.as_view(), name='order_item_delete'),
    path('order-notes/', OrderNoteListView.as_view(), name='order_notes_list'),
    path('order-notes/<str:pk>/', OrderNoteDetailViev.as_view(), name='order_note_detail'),
    path('order-notes/<str:pk>/update/', OrderNoteUpdateView.as_view(), name='order_note_update'),
    path('order-notes/<str:pk>/delete/', OrderNoteDeleteView.as_view(), name='order_note_delete'),
]
