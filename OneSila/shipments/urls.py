from django.urls import path
from .views import PackageListView, PackageDetailViev, PackageUpdateView, \
    PackageDeleteView, PackageItemListView, PackageItemDetailViev, \
    PackageItemUpdateView, PackageItemDeleteView, ShipmentListView, \
    ShipmentDetailViev, ShipmentUpdateView, ShipmentDeleteView, ShipmentItemListView, \
    ShipmentItemDetailViev, ShipmentItemUpdateView, ShipmentItemDeleteView, \
    ShipmentItemToShipListView, ShipmentItemToShipDetailViev, \
    ShipmentItemToShipUpdateView, ShipmentItemToShipDeleteView, ShipmentPickingListFileViev

app_name = 'shipments'

urlpatterns = [
    path('packages/', PackageListView.as_view(), name='packages_list'),
    path('packages/<str:pk>/', PackageDetailViev.as_view(), name='package_detail'),
    path('packages/<str:pk>/update/', PackageUpdateView.as_view(), name='package_update'),
    path('packages/<str:pk>/delete/', PackageDeleteView.as_view(), name='package_delete'),
    path('package-items/', PackageItemListView.as_view(), name='package_items_list'),
    path('package-items/<str:pk>/', PackageItemDetailViev.as_view(), name='package_item_detail'),
    path('package-items/<str:pk>/update/', PackageItemUpdateView.as_view(), name='package_item_update'),
    path('package-items/<str:pk>/delete/', PackageItemDeleteView.as_view(), name='package_item_delete'),
    path('shipments/', ShipmentListView.as_view(), name='shipments_list'),
    path('shipments/<str:pk>/', ShipmentDetailViev.as_view(), name='shipment_detail'),
    path('shipments/<str:pk>/pickinglist/', ShipmentPickingListFileViev.as_view(), name='shipment_pickinglist'),
    path('shipments/<str:pk>/update/', ShipmentUpdateView.as_view(), name='shipment_update'),
    path('shipments/<str:pk>/delete/', ShipmentDeleteView.as_view(), name='shipment_delete'),
    path('shipment-items/', ShipmentItemListView.as_view(), name='shipment_items_list'),
    path('shipment-items/<str:pk>/', ShipmentItemDetailViev.as_view(), name='shipment_item_detail'),
    path('shipment-items/<str:pk>/update/', ShipmentItemUpdateView.as_view(), name='shipment_item_update'),
    path('shipment-items/<str:pk>/delete/', ShipmentItemDeleteView.as_view(), name='shipment_item_delete'),
    path('shipment-item-to-ships/', ShipmentItemToShipListView.as_view(), name='shipment_item_to_ships_list'),
    path('shipment-item-to-ships/<str:pk>/', ShipmentItemToShipDetailViev.as_view(), name='shipment_item_to_ship_detail'),
    path('shipment-item-to-ships/<str:pk>/update/', ShipmentItemToShipUpdateView.as_view(), name='shipment_item_to_ship_update'),
    path('shipment-item-to-ships/<str:pk>/delete/', ShipmentItemToShipDeleteView.as_view(), name='shipment_item_to_ship_delete'),
]
