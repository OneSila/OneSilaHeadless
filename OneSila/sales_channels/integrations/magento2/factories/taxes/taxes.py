from sales_channels.factories.taxes.taxes import RemoteVatRateCreateFactory, RemoteVatRateUpdateFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models.taxes import MagentoTaxClass
from magento.models.tax import TaxClass


class MagentoTaxClassCreateFactory(GetMagentoAPIMixin, RemoteVatRateCreateFactory):
    remote_model_class = MagentoTaxClass
    remote_id_map = 'class_id'
    field_mapping = {
        'name': 'class_name'
    }

    default_field_mapping = {
        'class_type': TaxClass.CLASS_TYPE_PRODUCT
    }

    api_package_name = 'taxes'
    api_method_name = 'create'

    def get_tax_class_factory(self):
        from sales_channels.integrations.magento2.factories.taxes import MagentoTaxClassUpdateFactory
        return MagentoTaxClassUpdateFactory

    enable_fetch_and_update = True
    update_if_not_exists = True
    update_factory_class = property(get_tax_class_factory)

    def serialize_response(self, response):
        return response.to_dict()['data']

    def is_duplicate_error(self, error):
        return "already exists" in str(error)

    def customize_payload(self):
        self.payload = {'data': self.payload}
        return self.payload

    def fetch_existing_remote_data(self):
        tax_classes = self.api.taxes.all_in_memory()

        for tax_class in tax_classes:
            if tax_class.class_name == self.local_instance.name:
                return tax_class

        raise Exception(f'{self.local_instance.name} not found!')


class MagentoTaxClassUpdateFactory(GetMagentoAPIMixin, RemoteVatRateUpdateFactory):
    remote_model_class = MagentoTaxClass
    create_factory_class = MagentoTaxClassCreateFactory
    field_mapping = {
        'name': 'class_name'
    }

    def update_remote(self):
        self.magento_instance = self.api.taxes.by_id(self.remote_instance.remote_id)
        for key, value in self.payload.items():
            setattr(self.magento_instance, key, value)

        self.magento_instance.save()

    def serialize_response(self, response):
        return self.magento_instance.to_dict()
