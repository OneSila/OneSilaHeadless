import logging

from magento.exceptions import InstanceGetFailed

from properties.models import ProductProperty, Property
from sales_channels.factories.products.products import RemoteProductSyncFactory, RemoteProductCreateFactory, RemoteProductDeleteFactory, \
    RemoteProductUpdateFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.factories.products.eancodes import MagentoEanCodeUpdateFactory
from sales_channels.integrations.magento2.factories.products.images import MagentoMediaProductThroughCreateFactory, MagentoMediaProductThroughUpdateFactory, \
    MagentoMediaProductThroughDeleteFactory
from sales_channels.integrations.magento2.factories.properties.properties import MagentoProductPropertyCreateFactory, MagentoProductPropertyUpdateFactory, \
    MagentoProductPropertyDeleteFactory, MagentoAttributeSetCreateFactory
from sales_channels.integrations.magento2.models import MagentoProduct, MagentoInventory, MagentoPrice, MagentoProductContent, \
    MagentoProductProperty
from sales_channels.integrations.magento2.models.products import MagentoEanCode
from sales_channels.integrations.magento2.models.properties import MagentoAttributeSet
from magento.models import Product as MagentoApiProduct

from sales_channels.integrations.magento2.models.sales_channels import MagentoRemoteLanguage
from sales_channels.integrations.magento2.models.taxes import MagentoTaxClass
from sales_channels.models import SalesChannelViewAssign, RemoteCurrency

logger = logging.getLogger(__name__)

class MagentoProductSyncFactory(GetMagentoAPIMixin, RemoteProductSyncFactory):
    remote_model_class = MagentoProduct
    remote_product_property_class = MagentoProductProperty
    remote_product_property_create_factory = MagentoProductPropertyCreateFactory
    remote_product_property_update_factory = MagentoProductPropertyUpdateFactory
    remote_product_property_delete_factory = MagentoProductPropertyDeleteFactory

    remote_image_assign_create_factory = MagentoMediaProductThroughCreateFactory
    remote_image_assign_update_factory = MagentoMediaProductThroughUpdateFactory
    remote_image_assign_delete_factory = MagentoMediaProductThroughDeleteFactory

    remote_eancode_update_factory = MagentoEanCodeUpdateFactory

    def get_sync_product_factory(self):
        return MagentoProductSyncFactory

    def get_create_product_factory(self):
        from sales_channels.integrations.magento2.factories.products import MagentoProductCreateFactory
        return MagentoProductCreateFactory

    def get_delete_product_factory(self):
        from sales_channels.integrations.magento2.factories.products import MagentoProductDeleteFactory
        return MagentoProductDeleteFactory

    def get_add_variation_factory(self):
        from sales_channels.integrations.magento2.factories.products import MagentoProductVariationAddFactory
        return MagentoProductVariationAddFactory


    # Use the getter methods within the class where needed
    sync_product_factory = property(get_sync_product_factory)
    create_product_factory = property(get_create_product_factory)
    delete_product_factory = property(get_delete_product_factory)

    add_variation_factory = property(get_add_variation_factory)

    field_mapping = {
        'name': 'name',
        'sku': 'sku',
        'type': 'type_id',
        'active': 'status',
        'stock': 'stock',
        'allow_backorder': 'backorders',
        'visibility': 'visibility',
        'content': 'content',
        'assigns': 'views',
        'price': 'price',
        'discount': 'special_price',
        'vat_rate': 'tax_class_id',
        'url_key': 'url_key',
        'description': 'description',
        'short_description': 'short_description',
    }

    # Remote product types, to be set in specific layer implementations
    REMOTE_TYPE_SIMPLE = MagentoApiProduct.PRODUCT_TYPE_SIMPLE
    REMOTE_TYPE_CONFIGURABLE = MagentoApiProduct.PRODUCT_TYPE_CONFIGURABLE

    def is_accepted_variation_error(self, error):
        error_str = str(error)
        return 'already attached' in error_str or 'have the same set of attribute values' in error_str

    def get_unpacked_product_properties(self):
        custom_attributes = {}
        for remote_product_property in self.remote_product_properties:
            custom_attributes[remote_product_property.remote_property.attribute_code] = remote_product_property.remote_value

        return custom_attributes

    def set_visibility(self):
        if self.is_variation:
            self.set_variation_visibility()
        else:
            self.visibility = MagentoApiProduct.VISIBILITY_BOTH

        self.add_field_in_payload('visibility', self.visibility)

    def set_variation_visibility(self):
        self.visibility = MagentoApiProduct.VISIBILITY_NOT_VISIBLE

    def set_assigns(self):
        if self.is_variation:
            self.set_variation_assigns()
        else:
            self.assigns = list(
                map(int, SalesChannelViewAssign.objects.filter(
                    sales_channel=self.sales_channel,
                    product=self.local_instance
                ).values_list('sales_channel_view__remote_id', flat=True))
            )
        self.add_field_in_payload('assigns', self.assigns)


    def set_variation_assigns(self):
        self.assigns = list(
            map(int, SalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                product=self.parent_local_instance
            ).values_list('sales_channel_view__remote_id', flat=True))
        )

    def set_stock(self):
        return  # @TODO: Come back after we decide with inventory

        if self.remote_type == self.REMOTE_TYPE_CONFIGURABLE:
            self.stock = None
        else:
            self.stock = self.local_instance.inventory.salable()

        self.add_field_in_payload('stock', self.stock)

    def set_price(self):
        """Sets the price(s) for the product or variation in the payload, supporting multiple currencies."""

        self.prices_data = {}
        self.default_currency_code = None

        # For configurables, Magento expects no price info
        if self.remote_type == self.REMOTE_TYPE_CONFIGURABLE:
            self.price = None
            self.discount = None
            self.add_field_in_payload('price', self.price)
            self.add_field_in_payload('discount', self.discount)
            return

        from sales_channels.integrations.magento2.models import MagentoCurrency

        remote_currencies = MagentoCurrency.objects.filter(sales_channel=self.sales_channel).select_related(
            "local_instance")

        default_currency = remote_currencies.filter(is_default=True).first()

        for remote_currency in remote_currencies:
            local_currency = remote_currency.local_instance
            if not local_currency:
                continue

            full_price, discounted_price = self.local_instance.get_price_for_sales_channel(
                self.sales_channel, currency=local_currency
            )

            price = float(full_price) if full_price is not None else None
            discount = float(discounted_price) if discounted_price is not None else None

            self.prices_data[local_currency.iso_code] = {
                "price": price,
                "discount_price": discount,
            }

        # Set legacy price fields from default currency (for Magento backward compatibility)
        if default_currency and default_currency.local_instance:
            code = default_currency.local_instance.iso_code
            self.default_currency_code = code
            self.price = self.prices_data[code]['price']
            self.discount = self.prices_data[code]['discount_price']
            self.add_field_in_payload('price', self.price)
            self.add_field_in_payload('discount', self.discount)

    def set_vat_rate(self):
        self.vat_rate = None

        local_vat_rate = self.local_instance.vat_rate

        if local_vat_rate is None:
            self.vat_rate = None
            self.add_field_in_payload('vat_rate', self.vat_rate)
            return

        remote_vat_rate = MagentoTaxClass.objects.filter(
            sales_channel=self.sales_channel,
            local_instance=local_vat_rate
        ).first()


        if remote_vat_rate:
            self.vat_rate = remote_vat_rate.remote_id
            self.add_field_in_payload('vat_rate', self.vat_rate)
            return

        if local_vat_rate and not remote_vat_rate:
            from sales_channels.integrations.magento2.factories.taxes.taxes import MagentoTaxClassCreateFactory

            fac = MagentoTaxClassCreateFactory(
                sales_channel=self.sales_channel,
                local_instance=local_vat_rate,
                api=self.api
            )
            fac.run()

            self.vat_rate = fac.remote_instance.remote_id
            self.add_field_in_payload('vat_rate', self.vat_rate)

    def customize_payload(self):
        try:
            attribute_set = MagentoAttributeSet.objects.get(local_instance=self.rule, sales_channel=self.sales_channel)
        except MagentoAttributeSet.DoesNotExist:
            fac = MagentoAttributeSetCreateFactory(sales_channel=self.sales_channel, local_instance=self.rule)
            fac.run()

            attribute_set = fac.remote_instance

        self.payload['attribute_set_id'] = attribute_set.remote_id

        if self.remote_type == self.REMOTE_TYPE_CONFIGURABLE:
            self.payload['manage_stock'] = False

    def perform_remote_action(self):
        self.magento_product: MagentoApiProduct = self.api.products.by_sku(self.remote_instance.remote_sku)

        for key, value in self.payload.items():
            if  value != getattr(self.magento_product, key):
                setattr(self.magento_product, key, value)

        self.magento_product.save(scope='all')
        self.magento_product.update_custom_attributes(self.get_unpacked_product_properties())

    def get_remote_languages(self):
        sales_views_ids = SalesChannelViewAssign.objects.filter(sales_channel=self.sales_channel,
                                                                product=self.local_instance).values_list(
            'sales_channel_view_id', flat=True)

        return MagentoRemoteLanguage.objects.filter(
            sales_channel=self.sales_channel,
            sales_channel_view_id__in=sales_views_ids,
            store_view_code__isnull=False,
            local_instance__isnull=False
        )

    def process_content_translation(self, short_description, description, url_key, remote_language):
        self.magento_product.short_description = short_description
        self.magento_product.description = description
        self.magento_product.url_key = url_key
        self.magento_product.save(scope=remote_language.store_view_code)

    def update_multi_currency_prices(self):

        currencies_to_scope_map = {}
        for remote_currency in RemoteCurrency.objects.filter(sales_channel=self.sales_channel, local_instance__iso_code__in=self.prices_data.keys()):
            if len(remote_currency.store_view_codes):
                currencies_to_scope_map[remote_currency.local_instance.iso_code] = remote_currency.store_view_codes[0]

        for iso_code, current_price in self.prices_data.items():

            # the price was already created / updated
            if iso_code == self.default_currency_code:
                continue

            scope = currencies_to_scope_map.get(iso_code)
            price = current_price.get('price')
            discount_price = current_price.get('discount_price')

            self.magento_product.price = price
            self.magento_product.discount_price = discount_price
            self.magento_product.save(scope=scope)


    def final_process(self):
        translated_product_properties = ProductProperty.objects.filter(product=self.local_instance, property__is_public_information=True, property__type__in=Property.TYPES.TRANSLATED)

        # whe we update custom properties we only do it on main scope. The translated ones needs to be updated one by one in all languages
        for product_property in translated_product_properties:
            fac = MagentoProductPropertyUpdateFactory(sales_channel=self.sales_channel, local_instance=product_property, remote_product=self.remote_instance, api=self.api, skip_checks=True)
            fac.run()

class MagentoProductUpdateFactory(RemoteProductUpdateFactory, MagentoProductSyncFactory):
    fixing_identifier_class = MagentoProductSyncFactory

class MagentoProductCreateFactory(RemoteProductCreateFactory, MagentoProductSyncFactory):
    remote_inventory_class = MagentoInventory
    remote_price_class = MagentoPrice
    remote_product_content_class = MagentoProductContent
    remote_product_eancode_class = MagentoEanCode
    fixing_identifier_class = MagentoProductSyncFactory
    remote_id_map = 'id'

    api_package_name = 'products'
    api_method_name = 'create'

    def get_sync_product_factory(self):
        return MagentoProductSyncFactory

    sync_product_factory = property(get_sync_product_factory)

    def get_saleschannel_remote_object(self, sku):
        return self.api.products.by_sku(sku)

    def customize_payload(self):
        super().customize_payload()
        extra_data = {'custom_attributes': self.get_unpacked_product_properties()}
        self.payload = {'data': self.payload, 'extra_data': extra_data}

    def serialize_response(self, response):
        self.magento_product = response
        return response.to_dict()

class MagentoProductDeleteFactory(GetMagentoAPIMixin, RemoteProductDeleteFactory):
    remote_model_class = MagentoProduct
    delete_remote_instance = True

    def get_delete_product_factory(self):
        from sales_channels.integrations.magento2.factories.products import MagentoProductDeleteFactory
        return MagentoProductDeleteFactory

    remote_delete_factory = property(get_delete_product_factory)

    def delete_remote(self):

        try:
            magento_instance = self.api.products.by_sku(self.remote_instance.remote_sku)
        except InstanceGetFailed:
            return True

        return magento_instance.delete()

    def serialize_response(self, response):
        return response  # is True or False