from core.signals import ModelSignal

inventory_change = ModelSignal(use_caching=True)
inventory_received = ModelSignal(use_caching=True)
inventory_sent = ModelSignal(use_caching=True)
