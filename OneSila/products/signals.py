from django.db.models.signals import ModelSignal

product_created = ModelSignal(use_caching=True)
