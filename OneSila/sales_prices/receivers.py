from django.db.models.signals import post_save
from django.dispatch import receiver
from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem

import logging
logger = logging.getLogger(__name__)
