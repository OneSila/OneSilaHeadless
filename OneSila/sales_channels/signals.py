from django.db.models.signals import ModelSignal

# Post-Remote Signals
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

refresh_website_pull_models = ModelSignal(use_caching=True)
sales_channel_created = ModelSignal(use_caching=True)

create_remote_product = ModelSignal(use_caching=True)
update_remote_product = ModelSignal(use_caching=True)
sync_remote_product = ModelSignal(use_caching=True)
manual_sync_remote_product = ModelSignal(use_caching=True)
delete_remote_product = ModelSignal(use_caching=True)

sales_view_assign_updated = ModelSignal(use_caching=True)

update_remote_product_eancode = ModelSignal(use_caching=True)

create_remote_vat_rate = ModelSignal(use_caching=True)
update_remote_vat_rate = ModelSignal(use_caching=True)
