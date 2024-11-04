from core.signals import ModelSignal

create_remote_invoice = ModelSignal(use_caching=True)
create_remote_credit_note = ModelSignal(use_caching=True)