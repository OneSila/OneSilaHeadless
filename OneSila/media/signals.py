from django import dispatch
from django.db.models.signals import ModelSignal


cleanup_media_storage = ModelSignal(use_caching=True)
