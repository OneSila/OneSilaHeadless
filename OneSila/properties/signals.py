from django.db.models.signals import ModelSignal

product_properties_rule_created = ModelSignal(use_caching=True)
product_properties_rule_updated = ModelSignal(use_caching=True)
product_properties_rule_configurator_updated = ModelSignal(use_caching=True)
product_properties_rule_rename = ModelSignal(use_caching=True)