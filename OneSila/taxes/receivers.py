from django.db.models.signals import post_save
from django.dispatch import receiver
from taxes.models import Tax

import logging
logger = logging.getLogger(__name__)
