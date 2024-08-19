from core.signals import ModelSignal

draft = ModelSignal(use_caching=True)
todo = ModelSignal(use_caching=True)
in_progress = ModelSignal(use_caching=True)
done = ModelSignal(use_caching=True)
cancelled = ModelSignal(use_caching=True)