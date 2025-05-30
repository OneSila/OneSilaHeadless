from core.signals import ModelSignal

remote_instance_post_create = ModelSignal(use_caching=True)
remote_instance_post_update = ModelSignal(use_caching=True)
remote_instance_post_delete = ModelSignal(use_caching=True)

remote_instance_pre_create = ModelSignal(use_caching=True)
remote_instance_pre_update = ModelSignal(use_caching=True)
remote_instance_pre_delete = ModelSignal(use_caching=True)
