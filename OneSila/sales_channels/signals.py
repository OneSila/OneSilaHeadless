from django.db.models.signals import ModelSignal

# Post-Remote Signals
remote_instance_post_create = ModelSignal(use_caching=True)
remote_instance_post_update = ModelSignal(use_caching=True)
remote_instance_post_delete = ModelSignal(use_caching=True)

remote_instance_pre_create = ModelSignal(use_caching=True)
remote_instance_pre_update = ModelSignal(use_caching=True)
remote_instance_pre_delete = ModelSignal(use_caching=True)


create_remote_property = ModelSignal(use_caching=True)
update_remote_property = ModelSignal(use_caching=True)
delete_remote_property = ModelSignal(use_caching=True)


create_remote_property_select_value = ModelSignal(use_caching=True)
update_remote_property_select_value = ModelSignal(use_caching=True)
delete_remote_property_select_value = ModelSignal(use_caching=True)


create_remote_product_property = ModelSignal(use_caching=True)
update_remote_product_property = ModelSignal(use_caching=True)
delete_remote_product_property = ModelSignal(use_caching=True)