from django.db.models.signals import ModelSignal

price_changed = ModelSignal(use_caching=True)
