from django.utils.text import slugify
from magento.exceptions import InstanceCreateFailed, InstanceGetFailed

from sales_channels.factories.mixins import RemoteInstanceCreateFactory, RemoteInstanceUpdateFactory, RemoteInstanceDeleteFactory
from sales_channels.factories.properties.properties import RemotePropertyCreateFactory, RemotePropertyDeleteFactory, RemotePropertySelectValueCreateFactory, \
    RemotePropertySelectValueUpdateFactory, RemotePropertySelectValueDeleteFactory, RemotePropertyUpdateFactory, RemoteProductPropertyCreateFactory, \
    RemoteProductPropertyDeleteFactory, RemoteProductPropertyUpdateFactory
from sales_channels.integrations.magento2.constants import PROPERTY_FRONTEND_INPUT_MAP
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin, \
    MagentoEntityNotFoundGeneralErrorMixin, EnsureMagentoAttributeSetAttributesMixin, RemoteValueMixin, \
    MagentoTranslationMixin
from sales_channels.integrations.magento2.models import MagentoProperty, MagentoPropertySelectValue
from magento.models.product import ProductAttribute, Product
from sales_channels.integrations.magento2.models.properties import MagentoAttributeSet, MagentoAttributeSetAttribute, MagentoProductProperty


class MagentoPropertyCreateFactory(GetMagentoAPIMixin, MagentoEntityNotFoundGeneralErrorMixin, MagentoTranslationMixin, RemotePropertyCreateFactory):
    remote_model_class = MagentoProperty
    remote_id_map = 'attribute_id'
    # Key is the local field, value is the remote field
    field_mapping = {
        'add_to_filters': 'is_filterable',
        'name': 'default_frontend_label'
    }

    default_field_mapping = {
        'is_visible_on_front': True
    }

    api_package_name = 'product_attributes'
    api_method_name = 'create'
    enable_fetch_and_update = True
    update_if_not_exists = True
    update_factory_class = 'sales_channels.integrations.magento2.factories.properties.MagentoPropertyUpdateFactory'

    def get_attribute_code(self):
        return slugify(self.local_instance.name).replace('-', '_')

    def customize_payload(self):
        """
        Customizes the payload to include the correct 'frontend_input' mapping and wraps it under 'data'.
        """
        # Add 'frontend_input' mapping
        self.payload['frontend_input'] = PROPERTY_FRONTEND_INPUT_MAP.get(self.local_instance.type, ProductAttribute.TEXT)

        # we need to set it like this because of some issue with the order of the signals
        self.payload['attribute_code'] = self.get_attribute_code()
        self.payload['frontend_labels'] = self.get_frontend_labels(
            translations=self.local_instance.propertytranslation_set.all(),
            value_field='name',
            language=self.language
        )

        if self.payload['frontend_input'] == ProductAttribute.TEXT or self.payload['frontend_input'] == ProductAttribute.TEXTAREA:
            self.payload['scope'] = 'store'

        # Wrap the payload under the 'data' key as required by Magento's API
        self.payload = {'data': self.payload}
        return self.payload

    def serialize_response(self, response):
        return response.to_dict()

    def modify_remote_instance(self, response_data):
        self.remote_instance.attribute_code = response_data.get('data').get('attribute_code')

    def fetch_existing_remote_data(self):
        return self.api.product_attributes.by_code(self.get_attribute_code())


class MagentoPropertyUpdateFactory(GetMagentoAPIMixin, RemotePropertyUpdateFactory, MagentoTranslationMixin):
    remote_model_class = MagentoProperty
    create_factory_class = MagentoPropertyCreateFactory
    field_mapping = {
        'add_to_filters': 'is_filterable',
        'name': 'default_frontend_label'
    }

    def customize_payload(self):
        self.payload['frontend_labels'] = self.get_frontend_labels(
            translations=self.local_instance.propertytranslation_set.all(),
            value_field='name',
            language=self.language
        )

        return self.payload

    def update_remote(self):
        self.magento_instance = self.api.product_attributes.by_code(self.remote_instance.attribute_code)
        for key, value in self.payload.items():
            setattr(self.magento_instance, key, value)

        self.magento_instance.save()

    def serialize_response(self, response):
        self.magento_instance.refresh()
        return self.magento_instance.to_dict()


class MagentoPropertyDeleteFactory(GetMagentoAPIMixin, RemotePropertyDeleteFactory):
    remote_model_class = MagentoProperty
    delete_remote_instance = True

    def delete_remote(self):
        try:
            self.magento_instance = self.api.product_attributes.by_code(self.remote_instance.attribute_code)
        except InstanceGetFailed:
            return True

        return True if self.magento_instance is None else self.magento_instance.delete()

    def serialize_response(self, response):
        return response  # is True or False


class MagentoPropertySelectValueCreateFactory(GetMagentoAPIMixin, MagentoEntityNotFoundGeneralErrorMixin, MagentoTranslationMixin, RemotePropertySelectValueCreateFactory):
    remote_model_class = MagentoPropertySelectValue
    remote_property_factory = MagentoPropertyCreateFactory
    remote_id_map = 'data__value'
    field_mapping = {
        'value': 'label'
    }

    api_package_name = 'product_attribute_options'
    api_method_name = 'create'
    enable_fetch_and_update = True
    update_if_not_exists = True
    # update_factory_class = 'sales_channels.integrations.magento2.factories.properties.MagentoPropertySelectValueUpdateFactory'
    # FIXME: the line above is the full import.  Verify if the line below also works.
    update_factory_class = 'MagentoPropertySelectValueUpdateFactory'

    def preflight_check(self):
        return not self.local_instance.property.is_product_type

    def preflight_process(self):
        super().preflight_process()
        self.magento_property = self.api.product_attributes.by_code(self.remote_property.attribute_code)
        self.api.product_attribute_options_attribute = self.magento_property

    def customize_payload(self):
        """
        Customizes the payload to include the correct data format required by Magento's API.
        """
        self.payload = {
            'label': self.local_instance.value,
            'store_labels': self.get_frontend_labels(
                translations=self.local_instance.propertyselectvaluetranslation_set.all(),
                value_field='value',
                language=self.language
            )
        }
        self.payload = {'data': self.payload}
        return self.payload

    def serialize_response(self, response):
        return response.to_dict()

    def fetch_existing_remote_data(self):
        option = self.api.product_attribute_options.by_label(self.local_instance.value)

        if option is None:
            raise Exception(f'{self.local_instance.value} not found in {self.magento_property} options!')

        return option


class MagentoPropertySelectValueUpdateFactory(GetMagentoAPIMixin, MagentoTranslationMixin, RemotePropertySelectValueUpdateFactory):
    remote_model_class = MagentoPropertySelectValue
    create_factory_class = MagentoPropertySelectValueCreateFactory

    field_mapping = {
        'value': 'label'
    }

    def customize_payload(self):
        self.payload['store_labels'] = self.get_frontend_labels(
            translations=self.local_instance.propertyselectvaluetranslation_set.all(),
            value_field='value',
            language=self.language
        )

        return self.payload

    def preflight_check(self):
        return not self.local_instance.property.is_product_type

    def additional_update_check(self):
        # this we should do right before update so self.remote_instace is already there
        self.remote_property = self.remote_instance.remote_property.get_real_instance()
        self.magento_property = self.api.product_attributes.by_code(self.remote_property.attribute_code)
        self.api.product_attribute_options_attribute = self.magento_property

        return True

    def update_remote(self):
        self.magento_instance = self.api.product_attribute_options.by_id(self.remote_instance.remote_id)
        self.magento_instance.label = self.payload['label']
        self.magento_instance.store_labels = self.payload['store_labels']
        self.magento_instance.save()

    def serialize_response(self, response):
        return self.magento_instance.to_dict()


class MagentoPropertySelectValueDeleteFactory(GetMagentoAPIMixin, RemotePropertySelectValueDeleteFactory):
    remote_model_class = MagentoPropertySelectValue

    def delete_remote(self):
        self.remote_property = self.remote_instance.remote_property.get_real_instance()
        self.magento_property = self.api.product_attributes.by_code(self.remote_property.attribute_code)
        self.api.product_attribute_options_attribute = self.magento_property
        self.magento_instance = self.api.product_attribute_options.by_id(self.remote_instance.remote_id)

        return True if self.magento_instance is None else self.magento_instance.delete()

    def serialize_response(self, response):
        return response


class MagentoProductPropertyCreateFactory(GetMagentoAPIMixin, RemoteProductPropertyCreateFactory, RemoteValueMixin):
    remote_model_class = MagentoProductProperty
    remote_property_factory = MagentoPropertyCreateFactory
    remote_property_select_value_factory = MagentoPropertySelectValueCreateFactory
    enable_fetch_and_update = True
    update_if_not_exists = True
    update_factory_class = 'sales_channels.integrations.magento2.factories.properties.MagentoProductPropertyUpdateFactory'

    def create_remote(self):
        self.remote_value = self.get_remote_value()
        if self.get_value_only:
            self.remote_instance.remote_value = str(self.remote_value)
            self.remote_instance.save()
            return  # if we ony get the value we don't need to cotninue

        self.magento_product: Product = self.api.products.by_sku(self.remote_product.remote_sku)
        if isinstance(self.remote_value, dict):
            for remote_code, value in self.remote_value.items():
                self.magento_product.update_custom_attributes({self.remote_property.attribute_code: value}, scope=remote_code)
        else:
            self.magento_product.update_custom_attributes({self.remote_property.attribute_code: self.remote_value})

    def serialize_response(self, response):
        return {self.remote_property.attribute_code: self.remote_value}

    def upload_flow(self):
        """
        Flow to trigger the update factory. This can be overrided
        """
        update_factory = self.update_factory_class(self.integration,
                                                   self.local_instance,
                                                   api=self.api,
                                                   remote_instance=self.remote_instance,
                                                   remote_product=self.remote_product)
        update_factory.run()


class MagentoProductPropertyUpdateFactory(GetMagentoAPIMixin, RemoteValueMixin, RemoteProductPropertyUpdateFactory):
    remote_model_class = MagentoProductProperty
    create_factory_class = MagentoProductPropertyCreateFactory
    remote_property_factory = MagentoPropertyCreateFactory
    remote_property_select_value_factory = MagentoPropertySelectValueCreateFactory

    def update_remote(self):
        self.magento_product: Product = self.api.products.by_sku(self.remote_product.remote_sku)
        if isinstance(self.remote_value, dict):
            for remote_code, value in self.remote_value.items():
                self.magento_product.update_custom_attributes({self.remote_property.attribute_code: value}, scope=remote_code)
        else:
            self.magento_product.update_custom_attributes({self.remote_property.attribute_code: self.remote_value})

    def create_remote_instance(self):
        create_factory = self.create_factory_class(self.integration, self.local_instance, remote_product=self.remote_product)
        create_factory.run()

        self.remote_instance = create_factory.remote_instance

    def serialize_response(self, response):
        return {self.remote_property.attribute_code: self.remote_value}


class MagentoProductPropertyDeleteFactory(GetMagentoAPIMixin, RemoteProductPropertyDeleteFactory):
    remote_model_class = MagentoProductProperty
    delete_remote_instance = True

    def delete_remote(self):
        try:
            self.magento_product: Product = self.api.products.by_sku(self.remote_instance.remote_product.remote_sku)
        except InstanceGetFailed:
            return True  # if the product was deleted then is no need to delete the association

        self.magento_product.update_custom_attributes({self.remote_instance.remote_property.attribute_code: None})

    def serialize_response(self, response):
        return True


class MagentoAttributeSetCreateFactory(GetMagentoAPIMixin, MagentoEntityNotFoundGeneralErrorMixin, RemoteInstanceCreateFactory, EnsureMagentoAttributeSetAttributesMixin):
    remote_model_class = MagentoAttributeSet
    remote_id_map = 'attribute_set_id'
    field_mapping = {
        'product_type__value': 'attribute_set_name'
    }

    api_package_name = 'product_attribute_set'
    api_method_name = 'create'

    def get_update_attribute_set_factory(self):
        from sales_channels.integrations.magento2.factories.properties import MagentoAttributeSetUpdateFactory
        return MagentoAttributeSetUpdateFactory

    enable_fetch_and_update = True
    update_if_not_exists = True
    update_factory_class = "sales_channels.integrations.magento2.factories.properties.MagentoAttributeSetUpdateFactory"

    def customize_payload(self):
        """
        Customizes the payload to include the correct data format required by Magento's API.
        """
        self.payload['skeleton_id'] = self.sales_channel.attribute_set_skeleton_id
        self.payload = {'data': self.payload}
        return self.payload

    def serialize_response(self, response):
        return response.to_dict()

    def set_attribute_set_magento_instance(self):
        self.attribute_set_magento_instance = self.api.product_attribute_set.by_id(self.remote_instance.remote_id)

    def set_group_id(self):
        group = self.attribute_set_magento_instance.get_or_create_group_by_name('OneSila')
        self.remote_instance.group_remote_id = group.attribute_group_id
        self.remote_instance.save()

    def post_create_process(self):
        self.set_attribute_set_magento_instance()
        self.set_group_id()
        self.create_existing_attributes(self.remote_instance, self.attribute_set_magento_instance)

    def fetch_existing_remote_data(self):
        return self.api.product_attribute_set.by_name(self.local_instance.product_type.value)


class MagentoAttributeSetUpdateFactory(GetMagentoAPIMixin, RemoteInstanceUpdateFactory, EnsureMagentoAttributeSetAttributesMixin):
    remote_model_class = MagentoAttributeSet
    create_if_not_exists = True
    create_factory_class = MagentoAttributeSetCreateFactory
    field_mapping = {
        'product_type__value': 'attribute_set_name'
    }

    def __init__(self, sales_channel, local_instance, update_name_only=False, api=None, remote_instance=None):
        super().__init__(sales_channel, local_instance, api=api, remote_instance=remote_instance)
        self.update_name_only = update_name_only

    def update_remote(self):
        self.attribute_set_magento_instance = self.api.product_attribute_set.by_id(self.remote_instance.remote_id)
        for key, value in self.payload.items():
            setattr(self.attribute_set_magento_instance, key, value)

        self.attribute_set_magento_instance.save()

    def needs_update(self):
        return True  # we don't need to compare the payloads since this is sent by us when something actually changes

    def serialize_response(self, response):
        return self.attribute_set_magento_instance.to_dict()

    def remove_unnecessary_attributes(self, existing_ids):
        """
        Removes attributes from the Magento attribute set that are no longer in the existing list.
        Deletes the corresponding MagentoAttributeSetAttribute mirror instance.
        """
        # Fetch all MagentoAttributeSetAttribute instances related to the remote instance
        attribute_set_attributes = MagentoAttributeSetAttribute.objects.filter(magento_rule=self.remote_instance)

        for attribute in attribute_set_attributes:
            # Check if the remote_property.remote_id is not in the existing_ids
            if attribute.remote_property.remote_id not in existing_ids:

                try:
                    self.attribute_set_magento_instance.remove_attribute_set_attribute(attribute.remote_property.attribute_code)
                except Exception as e:
                    # if it was directly from the server we skip it
                    if "wasn't found" in str(e):
                        pass
                    elif "attributeCode doesn't exist" in str(e):
                        fac = MagentoPropertyDeleteFactory(sales_channel=self.sales_channel, local_instance=attribute.remote_property.local_instance)
                        fac.run()
                    else:
                        raise

                attribute.delete()

    def update_attribute_set_attributes_sort_order(self):
        attribute_set_attributes = MagentoAttributeSetAttribute.objects.filter(magento_rule=self.remote_instance)

        sort_order_dict = {}
        for attribute in attribute_set_attributes:
            sort_order_dict[attribute.remote_property.attribute_code] = attribute.local_instance.sort_order

        self.attribute_set_magento_instance.update_attribute_sort_orders(self.remote_instance.group_remote_id, sort_order_dict)

    def post_update_process(self):

        if self.update_name_only:
            return

        existing_ids = self.create_existing_attributes(self.remote_instance, self.attribute_set_magento_instance)
        self.remove_unnecessary_attributes(existing_ids)

        # ATM the API doesn't allow that and removing and re-creating deletes the actual product properties
        # on the product so we have no way to do this right now
        # self.update_attribute_set_attributes_sort_order()


class MagentoAttributeSetDeleteFactory(GetMagentoAPIMixin, RemoteInstanceDeleteFactory):
    remote_model_class = MagentoAttributeSet
    delete_remote_instance = True

    def delete_remote(self):
        magento_instance = self.api.product_attribute_set.by_id(self.remote_instance.remote_id)

        return True if magento_instance is None else magento_instance.delete()

    def serialize_response(self, response):
        return response  # is True or False
