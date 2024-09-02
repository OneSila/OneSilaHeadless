from django import dispatch
from django.db.models.signals import ModelSignal, post_save


registered = ModelSignal(use_caching=True)
invited = ModelSignal(use_caching=True)
invite_accepted = ModelSignal(use_caching=True)
disabled = ModelSignal(use_caching=True)
enabled = ModelSignal(use_caching=True)
login_token_requested = ModelSignal(use_caching=True)
recovery_token_created = ModelSignal(use_caching=True)
password_changed = ModelSignal(use_caching=True)
post_create = ModelSignal(use_caching=True)
post_update = ModelSignal(use_caching=True)

mutation_update = ModelSignal(use_caching=True)
mutation_create = ModelSignal(use_caching=True)
