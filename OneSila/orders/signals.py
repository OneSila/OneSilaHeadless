from core.signals import ModelSignal

draft = ModelSignal(use_caching=True)
pending_processing = ModelSignal(use_caching=True)
pending_shipping = ModelSignal(use_caching=True)
pending_shipping_approval = ModelSignal(use_caching=True)
to_ship = ModelSignal(use_caching=True)
await_inventory = ModelSignal(use_caching=True)
shipped = ModelSignal(use_caching=True)
hold = ModelSignal(use_caching=True)
cancelled = ModelSignal(use_caching=True)
pending_invoice = ModelSignal(use_caching=True)
