from django.urls import path
from .views import PurchaseOrderListView, PurchaseOrderDetailViev, PurchaseOrderUpdateView, PurchaseOrderDeleteView, PurchaseOrderItemListView, PurchaseOrderItemDetailViev, PurchaseOrderItemUpdateView, PurchaseOrderItemDeleteView, SupplierProductListView, SupplierProductDetailViev, SupplierProductUpdateView, SupplierProductDeleteView

app_name = 'purchasing'

urlpatterns = [
    path('purchase-orders/', PurchaseOrderListView.as_view(), name='purchase_orders_list'),
    path('purchase-orders/<str:pk>/', PurchaseOrderDetailViev.as_view(), name='purchase_order_detail'),
    path('purchase-orders/<str:pk>/update/', PurchaseOrderUpdateView.as_view(), name='purchase_order_update'),
    path('purchase-orders/<str:pk>/delete/', PurchaseOrderDeleteView.as_view(), name='purchase_order_delete'),
    path('purchase-order-items/', PurchaseOrderItemListView.as_view(), name='purchase_order_items_list'),
    path('purchase-order-items/<str:pk>/', PurchaseOrderItemDetailViev.as_view(), name='purchase_order_item_detail'),
    path('purchase-order-items/<str:pk>/update/', PurchaseOrderItemUpdateView.as_view(), name='purchase_order_item_update'),
    path('purchase-order-items/<str:pk>/delete/', PurchaseOrderItemDeleteView.as_view(), name='purchase_order_item_delete'),
    path('supplier-products/', SupplierProductListView.as_view(), name='supplier_products_list'),
    path('supplier-products/<str:pk>/', SupplierProductDetailViev.as_view(), name='supplier_product_detail'),
    path('supplier-products/<str:pk>/update/', SupplierProductUpdateView.as_view(), name='supplier_product_update'),
    path('supplier-products/<str:pk>/delete/', SupplierProductDeleteView.as_view(), name='supplier_product_delete'),
]
