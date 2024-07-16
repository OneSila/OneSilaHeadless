from django.db.models.signals import post_save
from django.dispatch import receiver
from inventory.models import Inventory, InventoryLocation

import logging
logger = logging.getLogger(__name__)
