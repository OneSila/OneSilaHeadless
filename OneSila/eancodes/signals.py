from django.db.models.signals import ModelSignal

ean_code_released_for_product = ModelSignal(use_caching=True)