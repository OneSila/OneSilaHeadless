from core.signals import ModelSignal

draft = ModelSignal(use_caching=True)
to_order = ModelSignal(use_caching=True)
ordered = ModelSignal(use_caching=True)
confirmed = ModelSignal(use_caching=True)
pending_delivery = ModelSignal(use_caching=True)
delivered = ModelSignal(use_caching=True)
