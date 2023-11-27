from django import dispatch
from django.db.models.signals import ModelSignal

registered = ModelSignal(use_caching=True)
invite_sent = ModelSignal(use_caching=True)
invite_accepted = ModelSignal(use_caching=True)
