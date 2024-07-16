from django.db.models.signals import post_save
from django.dispatch import receiver
from media.models import Media, Image, Video

import logging
logger = logging.getLogger(__name__)
