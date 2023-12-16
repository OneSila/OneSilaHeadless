from django.urls import path
from .views import InventoryListView, InventoryLocationListView, InventoryDetailViev, InventoryLocationDetailViev, InventoryUpdateView, InventoryLocationUpdateView, InventoryDeleteView, InventoryLocationDeleteView


app_name = 'inventory'

urlpatterns = [
    path('inventories/', InventoryListView.as_view(), name='inventories_list'),
    path('inventories/<str:pk>/', InventoryDetailViev.as_view(), name='inventory_detail'),
    path('inventories/<str:pk>/update/', InventoryUpdateView.as_view(), name='inventory_update'),
    path('inventories/<str:pk>/delete/', InventoryDeleteView.as_view(), name='inventory_delete'),
    path('inventory-locations/', InventoryLocationListView.as_view(), name='inventory_locations_list'),
    path('inventory-locations/<str:pk>/', InventoryLocationDetailViev.as_view(), name='inventory_location_detail'),
    path('inventory-locations/<str:pk>/update/', InventoryLocationUpdateView.as_view(), name='inventory_location_update'),
    path('inventory-locations/<str:pk>/delete/', InventoryLocationDeleteView.as_view(), name='inventory_location_delete'),
]
