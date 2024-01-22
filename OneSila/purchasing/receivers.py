from django.db.models.signals import post_save
from django.dispatch import receiver
from purchasing.models import SupplierProduct, PurchaseOrder, PurchaseOrderItem

import logging
logger = logging.getLogger(__name__)
