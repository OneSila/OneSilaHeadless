from imports_exports.factories.imports import ImportMixin

from core.helpers import clean_json_data
from imports_exports.factories.products import ImportProductInstance
from sales_channels.models import ImportProduct
from django.contrib.contenttypes.models import ContentType
from imports_exports.factories.properties import ImportPropertySelectValueInstance
from sales_channels.models import ImportPropertySelectValue

import logging
logger = logging.getLogger(__name__)


class SalesChannelImportMixin(ImportMixin):
    """
    When subsclassing this ImportMixin there are a few things to realise:
    1. You are importing data from your remote channel into your local data AND
        creating the mirror models.  From time to time, the payload needs to
        match with the push factory payloads from your integration.
    2. You will need to set the remote classes to ensure the handle_xxx will work correctly.
       If you do not set them, the importer will raise NotImplementedError .
    3. There are also a fet get_xxx methods that will need creating.  Each of them will
       raise NotImplementedError if not implemented.  If you dont need them, return []

    Expected remote_classes:
    - remote_ean_code_class
    - remote_product_content_class
    - remote_imageproductassociation_class
    - remote_price_class

    Expected get_xxx methods:
    - get_total_instances
    - get_properties_data
    - get_select_values_data
    - get_rules_data

    If you do not need some of these handlers.  Either:
    - override the handle_xxx method and leave it empty.
    - override the import_products_process method and remove the handlers you do not need.


    What does the handl_xxx do?
    - it is used to convert the importinstance thing into mirror model data.  So it needs to be the
    same as the push model data that is used later on in the integration itself.


    What does all of the get_xxx do?
    It will convert the original (product) data and convert it into it's own block that goes
    into the universal json format:

        data = {
            "name": "Ultimate Product",
            "sku": "ALL001",
            "type": Product.SIMPLE,
            "product_type": "Chair",
            "ean_code": "111222333",
            "vat_rate": 19,
            "active": True,
            "allow_backorder": False,
            "translations": [
                {
                    "short_description": "All features",
                    "description": "This product has everything.",
                    "url_key": "ultimate-product"
                }
            ],
            "attributes": [
                { "property_data": { "name": "Material", "type": "SELECT" }, "value": "Red" },
                { "property_data": { "name": "Style", "type": "SELECT" }, "value": "Elegant" }
            ],
            "images": [
                { "image_url": "https://2.img-dpreview.com/files/p/E~C1000x0S4000x4000T1200x1200~articles/3925134721/0266554465.jpeg" },
                { "image_url": "https://vgl.ucdavis.edu/sites/g/files/dgvnsk15116/files/styles/sf_landscape_4x3/public/images/marketing_highlight/Sample-Collection-Box-Cat-640px.jpg", "is_main_image": True }
            ],
            "prices": [
                { "price": 29.99, "currency": "EUR" },
                { "rrp": 34.99, "currency": "USD" }
            ],
        }

    so get_prices, will compile the data['prices'] block.

    """

    import_properties = True
    import_select_values = True
    import_rules = True
    import_products = True

    def __init__(self, import_process, sales_channel, language=None):
        super().__init__(import_process, language)

        self.sales_channel = sales_channel
        self.initial_sales_channel_status = sales_channel.active
        self.api = self.get_api()

    def prepare_import_process(self):
        """
        Ensure that you take the neccessary steps to safegaurd the import process and local data.
        This is by default, disabling channels to prevent people updating products while you are
        importing data and preventing mirror models from creating sync loops.
        """
        # during the import this needs to stay false to prevent trying to create the mirror models because
        # we create them manually
        self.sales_channel.active = False
        self.sales_channel.is_importing = True
        self.sales_channel.save()

    def get_remote_model_class(self, model_name: str):
        try:
            return getattr(self, model_name)
        except AttributeError:
            raise AttributeError(f"remote_model_class {model_name} not set on {self.__class__.__name__}")

    def get_total_instances(self):
        raise NotImplementedError("get_total_instances not implemented")

    def get_properties_data(self):
        raise NotImplementedError("get_properties_data not implemented")

    def get_select_values_data(self):
        raise NotImplementedError("get_select_values_data not implemented")

    def get_rules_data(self):
        raise NotImplementedError("get_rules_data not implemented")

    def get_product_data(self, import_instance: ImportProductInstance):
        raise NotImplementedError("get_product_data not implemented")

    def create_log_instance(self, import_instance: ImportProductInstance, structured_data: dict):
        log_instance = ImportProduct.objects.create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            import_process=self.import_process,
            remote_product=import_instance.remote_instance,
            raw_data=clean_json_data(import_instance.data),
            structured_data=clean_json_data(structured_data),
            successfully_imported=True
        )

        log_instance.content_type = ContentType.objects.get_for_model(import_instance.instance)
        log_instance.object_id = import_instance.instance.pk

    def update_select_value_log_instance(self, log_instance: ImportPropertySelectValue,
                                         import_instance: ImportPropertySelectValueInstance):
        mirror_property_select_value = import_instance.remote_instance

        log_instance.successfully_imported = True
        log_instance.content_type = ContentType.objects.get_for_model(import_instance.instance)
        log_instance.object_id = import_instance.instance.pk

        if mirror_property_select_value:
            log_instance.remote_property_value = mirror_property_select_value

        log_instance.save()

        if mirror_property_select_value and not mirror_property_select_value.remote_id:
            mirror_property_select_value.remote_id = log_instance.raw_data['value']
            mirror_property_select_value.save()

    def handle_ean_code(self, import_instance: ImportProductInstance):
        EanCodeClass = self.get_remote_model_class('remote_ean_code_class')
        instance, _ = EanCodeClass.objects.get_or_create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=import_instance.remote_instance,
        )

        if hasattr(import_instance, 'ean_code'):
            if instance.ean_code != import_instance.ean_code:
                instance.ean_code = import_instance.ean_code
                instance.save()

    def handle_translations(self, import_instance: ImportProductInstance):
        TranslationClass = self.get_remote_model_class('remote_product_content_class')
        if hasattr(import_instance, 'translations'):
            TranslationClass.objects.get_or_create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_product=import_instance.remote_instance,
            )

    def handle_images(self, import_instance: ImportProductInstance):
        RemoteImageProductAssociationClass = self.get_remote_model_class('remote_imageproductassociation_class')

        if hasattr(import_instance, 'images'):
            remote_id_map = import_instance.data.get('__image_index_to_remote_id', {})

            for index, image_ass in enumerate(import_instance.images_associations_instances):
                image_association, _ = RemoteImageProductAssociationClass.objects.get_or_create(
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    local_instance=image_ass,
                    remote_product=import_instance.remote_instance,
                )

                remote_id = remote_id_map.get(str(index))
                if remote_id and not image_association.remote_id:
                    image_association.remote_id = remote_id
                    image_association.save()

    def handle_prices(self, import_instance: ImportProductInstance):
        RemotePriceClass = self.get_remote_model_class('remote_price_class')

        if not hasattr(import_instance, 'prices'):
            return

        remote_product = import_instance.remote_instance

        instance, _ = RemotePriceClass.objects.get_or_create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=remote_product,
        )

        price_data = {}

        for price_entry in import_instance.prices:
            currency = price_entry.get("currency")
            price = price_entry.get("price")
            rrp = price_entry.get("rrp")

            data = {}
            if rrp is not None:
                data["price"] = float(rrp)
            if price is not None:
                data["discount_price"] = float(price)

            if data:
                price_data[currency] = data

        if price_data:
            instance.price_data = price_data
            instance.save()

    def process_completed(self):
        self.sales_channel.active = self.initial_sales_channel_status
        self.sales_channel.is_importing = False
        self.sales_channel.save()
