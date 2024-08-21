from core.documents.views import DocumentViev
from core.views import EmptyTemplateView
from .models import Package, PackageItem, Shipment, ShipmentItem, ShipmentItemToShip


class ShipmentPickingListFileViev(DocumentViev):
    model = Shipment


class PackageListView(EmptyTemplateView):
    pass


class PackageDetailViev(EmptyTemplateView):
    pass


class PackageUpdateView(EmptyTemplateView):
    pass


class PackageDeleteView(EmptyTemplateView):
    pass


class PackageItemListView(EmptyTemplateView):
    pass


class PackageItemDetailViev(EmptyTemplateView):
    pass


class PackageItemUpdateView(EmptyTemplateView):
    pass


class PackageItemDeleteView(EmptyTemplateView):
    pass


class ShipmentListView(EmptyTemplateView):
    pass


class ShipmentDetailViev(EmptyTemplateView):
    pass


class ShipmentUpdateView(EmptyTemplateView):
    pass


class ShipmentDeleteView(EmptyTemplateView):
    pass


class ShipmentItemListView(EmptyTemplateView):
    pass


class ShipmentItemDetailViev(EmptyTemplateView):
    pass


class ShipmentItemUpdateView(EmptyTemplateView):
    pass


class ShipmentItemDeleteView(EmptyTemplateView):
    pass


class ShipmentItemToShipListView(EmptyTemplateView):
    pass


class ShipmentItemToShipDetailViev(EmptyTemplateView):
    pass


class ShipmentItemToShipUpdateView(EmptyTemplateView):
    pass


class ShipmentItemToShipDeleteView(EmptyTemplateView):
    pass
