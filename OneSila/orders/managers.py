from core import models
from core.managers import MultiTenantQuerySet, MultiTenantManager
from core.models import Sum, F, FloatField, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from products.models import Product

from datetime import timedelta

import logging
logger = logging.getLogger(__name__)


# ##### #
# Order #
# ##### #

class OrderQuerySet(MultiTenantQuerySet):
    def unprocessed(self):
        return self.filter(status__in=self.model.UNPROCESSED)

    def exclude_cancelled(self):
        return self.exclude(status=self.model.CANCELLED)

    def hold(self):
        return self.filter(status__in=self.model.HOLD)

    def annotate_order_value(self):
        return self.annotate(order_value=Sum(F('orderitem__quantity') * F('orderitem__price'), output_field=FloatField()))


class OrderManager(MultiTenantManager):
    def get_queryset(self):
        return OrderQuerySet(self.model, using=self._db).\
            annotate_order_value()

    def unprocessed(self):
        return self.get_queryset().unprocessed()

    def exclude_cancelled(self):
        return self.get_queryset().exclude_cancelled()

    def hold(self):
        return self.get_queryset().hold()


# ########## #
# Order Item #
# ########## #

class OrderItemQuerySet(MultiTenantQuerySet):

    def total_value(self):
        '''
        is the sum of all price * quantity
        '''
        total_value_aggregate = self.all().aggregate(total_value=Sum(F('quantity') * F('price'), output_field=FloatField()))
        return round(total_value_aggregate['total_value'], 2) if total_value_aggregate['total_value'] is not None else 0

    def filter_sold_in_x_days(self, x_days=21):
        '''
        Contrary to sold_in_last_x_days, this just filters and doesnt expect you to give a product
        '''
        x_days_ago = timezone.now() - timedelta(days=x_days)
        return self.filter(order__created_at__gt=x_days_ago)

    def sold_in_last_x_days(self, product, x_days=21):
        x_days_ago = timezone.now() - timedelta(days=x_days)
        qty = self.filter(
            product=product,
            order__created_at__gt=x_days_ago).aggregate(Sum('quantity'))['quantity__sum']
        return qty

    def annotate_total_row_value(self):
        return self.annotate(total_value=Sum(F('quantity') * F('price'), output_field=FloatField()))


class OrderItemManager(MultiTenantManager):
    def get_queryset(self):
        return OrderItemQuerySet(self.model, using=self._db)  # Important!

    def total_value(self):
        return self.get_queryset().total_value()

    def filter_sold_in_x_days(self, x_days=21):
        return self.get_queryset().filter_sold_in_x_days(x_days)

    def sold_in_last_x_days(self, product, x_days=21):
        return self.get_queryset().sold_in_last_x_days(product, x_days)
