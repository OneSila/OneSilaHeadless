from django import dispatch
from django.db.models.signals import ModelSignal


exchange_rate_change = ModelSignal(use_caching=True)
