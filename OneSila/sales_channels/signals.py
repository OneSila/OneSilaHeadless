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

update_remote_inventory = ModelSignal(use_caching=True)

update_remote_price = ModelSignal(use_caching=True)

update_remote_product_content = ModelSignal(use_caching=True)

add_remote_product_variation = ModelSignal(use_caching=True)
remove_remote_product_variation = ModelSignal(use_caching=True)

create_remote_image_association = ModelSignal(use_caching=True)
update_remote_image_association = ModelSignal(use_caching=True)
delete_remote_image_association = ModelSignal(use_caching=True)

delete_remote_image = ModelSignal(use_caching=True)