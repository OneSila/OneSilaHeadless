from django import dispatch
from django.db.models.signals import ModelSignal


exchange_rate_official__pre_save = ModelSignal(use_caching=True)
exchange_rate_official__post_save = ModelSignal(use_caching=True)

exchange_rate__pre_save = ModelSignal(use_caching=True)
exchange_rate__post_save = ModelSignal(use_caching=True)
