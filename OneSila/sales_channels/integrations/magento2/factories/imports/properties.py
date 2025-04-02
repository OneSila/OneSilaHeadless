from imports_exports.factories.properties import ImportProductPropertiesRuleInstance, \
    ImportProductPropertiesRuleItemInstance
from sales_channels.integrations.magento2.models import MagentoProperty
from sales_channels.integrations.magento2.models.properties import MagentoAttributeSet, MagentoAttributeSetAttribute


class ImportMagentoProductPropertiesRuleInstance(ImportProductPropertiesRuleInstance):
    def __init__(self, data: dict, import_process=None, product_type=None, sales_channel=None):
        super().__init__(data, import_process, product_type=product_type)

        self.sales_channel = sales_channel
        self.mirror_model_class = MagentoAttributeSet
        self.mirror_model_map = {
                "local_instance": "*",
            }

    def before_process_item_logic(self, item_import_instance: ImportProductPropertiesRuleItemInstance):

        remote_property = MagentoProperty.objects.get(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            local_instance=item_import_instance.property
        )

        item_import_instance.prepare_mirror_model_class(
            mirror_model_class=MagentoAttributeSetAttribute,
            sales_channel=self.sales_channel,
            mirror_model_map= {
                "local_instance": "*",
            },
            mirror_model_defaults={
                "magento_rule": self.remote_instance,
                "remote_property": remote_property,
                "remote_id": remote_property.remote_id
            }
        )