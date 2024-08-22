import operator
from django.db.models import Case, When, F, Value
from core import models
from core.models import Sum
from core.managers import MultiTenantQuerySet, MultiTenantManager
from orders.models import Order
from contacts.models import ShippingAddress
from products.models import Product, BundleVariation
from products.product_types import HAS_INDIRECT_INVENTORY_TYPES, \
    HAS_DIRECT_INVENTORY_TYPES, BUNDLE

import logging
logger = logging.getLogger(__name__)


class InventoryQuerySet(MultiTenantQuerySet):
    def order_by_least(self):
        return self.order_by("quantity")

    def find_inventory_shippingaddresses(self):
        # You cant directly filter for the product from the qs
        # as the inventory can be assigned in many ways.
        qs = self.filter_physical()
        shippingaddress_ids = qs.values('inventorylocation__shippingaddress')
        return ShippingAddress.objects.filter(id__in=shippingaddress_ids)

    def filter_by_shippingaddress(self, shippingaddress):
        return self.filter(inventorylocation__shippingaddress=shippingaddress)

    def order_by_relevant_shippinglocation(self, country_code):
        # FIXME: This could really do with sorting out some kind of distance
        # from the country_code somewhow.
        return self.annotate(
            country=F('inventorylocation__shippingaddress__country'),
            is_relevant_country=Case(
                When(country=Value(country_code), then=1),
                default=2,
                output_field=models.IntegerField()
            )
        ).order_by('-is_relevant_country', '-inventorylocation__shippingaddress')

    def filter_internal(self):
        """Filter to only return inventory thats attached to an internal shipping address"""
        return self.filter(inventorylocation__shippingaddress__company__is_internal_company=True)

    def determine_picking_locations(self, product, shipping_address, quantity) -> dict:
        """
        Find the locations with the quantity untill you run out of quanity.
        Used for picking goods.

        Returns a dict
        """
        locations = list(self.filter(
            multi_tenant_company=product.multi_tenant_company,
            inventorylocation__shippingaddress=shipping_address,
            product=product,
        ))
        d = {}

        while quantity:
            loc = locations.pop()
            available_qty = loc.quantity

            if available_qty <= quantity:
                d[loc] = available_qty
                quantity -= available_qty
            else:
                d[loc] = quantity
                quantity = 0

        return d

    def filter_physical(self, product=None):
        """ Return the inventories where a given product is located."""
        if product is None:
            product = self._hints['instance']

        multi_tenant_company = product.multi_tenant_company

        if product.type in HAS_DIRECT_INVENTORY_TYPES:
            return self.filter(quantity__gt=0, multi_tenant_company=multi_tenant_company)

        if product.type in HAS_INDIRECT_INVENTORY_TYPES:
            supplier_product_ids = product.supplier_products.\
                filter(multi_tenant_company=multi_tenant_company).\
                values('id')
            return self.model.objects.\
                filter(product_id__in=supplier_product_ids, multi_tenant_company=multi_tenant_company)

        if product.type in [BUNDLE]:
            # FIXME: What to do about bundle-products?  Nested? Or parts with querysets?
            # This should be the inventory(ies) of the product that is least available as we need the
            # min availble products.

            # NOTE This will NOT return the real availabiltiy as this should be divided by
            # the quantity on the BundleVariation.
            variations = BundleVariation.objects.filter(parent=product)
            variation_physicals = {i.variation: i.variation.inventory.physical() for i in variations}
            # sorted will return a list of tuples.  Eg [(variation, physical_stock), ...].
            least_stock_product = sorted(variation_physicals.items(), key=operator.itemgetter(1), reverse=False)[0][0]
            return least_stock_product.inventory.filter_physical()

    def physical(self):
        """
        Physically on stock, could be reserved, could be salable.
        Configurable products return 0, as they cannot hold physical stock.
        """

        # Calculate your directly attached inventory (For manufacturable products)
        product = self._hints['instance']
        multi_tenant_company = product.multi_tenant_company

        if product.type in HAS_DIRECT_INVENTORY_TYPES or product.type in HAS_INDIRECT_INVENTORY_TYPES:
            inventory_qs = self.filter_physical()
            return inventory_qs.aggregate(Sum('quantity'))['quantity__sum'] or 0

        # put the qty here so configurable products to have 0 instead of error
        qty = 0
        if product.type in [BUNDLE]:
            # Even though we can attach a variety of bundles, we must ensure we
            # dont sum them, but use min.  Why? Let's take an example. A bundle existing of a phone + 2 covers:
            # Phone: 100 items
            # Cover: 30
            # That means we can only ship 15x Phone+cover since the cover only has 30 pieces of which 2 are needed.
            try:
                # int() will round down which is what we want.
                available_parts = []
                for through in BundleVariation.objects.filter(parent=product, multi_tenant_company=multi_tenant_company):
                    physical = through.variation.inventory.physical()
                    available_parts.append(int(physical / through.quantity))

                qty += min(available_parts)
            except ValueError:
                pass

        return qty

    def salable(self):
        """Items that are available for sale"""
        if self._hints['instance'].allow_backorder:
            return self.model._meta.backorder_item_count

        physical = self.physical()
        salable = physical - self.reserved()

        return salable

    def reserved(self):
        """Items that have been sold but not shipped"""
        product = self._hints['instance']
        multi_tenant_company = product.multi_tenant_company

        sold_agg = product.orderitem_set.\
            filter(
                multi_tenant_company=multi_tenant_company,
                order__status__in=Order.DONE_TYPES
            ).\
            distinct().\
            aggregate(Sum('quantity'))['quantity__sum'] or 0

        return sold_agg


class InventoryManager(MultiTenantManager):
    def get_queryset(self):
        return InventoryQuerySet(self.model, using=self._db)

    def order_by_least(self):
        return self.get_queryset().order_by_least()

    def salable(self):
        return self.get_queryset().salable()

    def physical(self):
        return self.get_queryset().physical()

    def reserved(self):
        return self.get_queryset().reserved()

    def filter_physical(self, product=None):
        return self.get_queryset().filter_physical(product=product)

    def filter_internal(self):
        return self.get_queryset().filter_internal()

    def find_inventory_shippingaddresses(self):
        return self.get_queryset().find_inventory_shippingaddresses()

    def filter_by_shippingaddress(self, shippingaddress):
        return self.get_queryset().filter_by_shippingaddress(shippingaddress=shippingaddress)

    def order_by_relevant_shippinglocation(self, country_code):
        return self.get_queryset().order_by_relevant_shippinglocation(country_code=country_code)

    def determine_picking_locations(self, product, shipping_address, qty):
        return self.get_queryset().determine_picking_locations(product, shipping_address, qty)


class InventoryLocationQuerySet(MultiTenantQuerySet):
    def annotate_is_external_location(self):
        return self.annotate(is_internal_location=F('shippingaddress__company__is_internal_company'))

    def filter_by_shippingaddress_set(self, shippingaddress_set):
        return self.filter(shippingaddress__in=shippingaddress_set)

    def filter_locations_for_product(self, product):
        # this all needs tranlating into either manufacturable or supplier products to get the right locations.
        if product.is_manufacturable() or product.is_supplier_product():
            return self.filter(multi_tenant_company=multi_tenant_company,
                product=product)
        elif product.is_simple():
            products = product.supplier_products.all()
            return self.filter(inventory__product__in=products)
        elif product.is_bundle():
            products = product.deflate_bundle()
            location_ids = []

            for p in products:
                for location in self.filter_locations_for_product(p):
                    location_ids.append(location.id)

            return self.filter(id__in=location_ids)
        else:
            raise ValueError(f"Product type {produt.type} not implemented.")


class InventoryLocationManager(MultiTenantManager):
    def get_queryset(self):
        return InventoryLocationQuerySet(self.model, using=self._db).\
            annotate_is_external_location()

    def filter_by_shippingaddress_set(self, shippingaddress_set):
        return self.get_queryset().filter_by_shippingaddress_set(shippingaddress_set)

    def filter_locations_for_product(product, qty):
        return self.get_queryset().filter_locations_for_product(product, qty)
