from django.db.models.signals import post_save
from django.dispatch import receiver
from eancodes.models import EanCode

import logging
logger = logging.getLogger(__name__)
