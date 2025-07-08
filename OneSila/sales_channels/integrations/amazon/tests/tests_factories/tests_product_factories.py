from types import SimpleNamespace
from unittest.mock import patch, MagicMock
import json

from model_bakery import baker

from core.tests import TestCase
from core.tests import TransactionTestCase
from sales_channels.integrations.amazon.factories import AmazonProductDeleteFactory

from sales_channels.models.sales_channels import SalesChannelViewAssign
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonRemoteLanguage,
)
from sales_channels.integrations.amazon.models.products import AmazonProduct
from sales_channels.integrations.amazon.models.properties import (
    AmazonProperty,
    AmazonPublicDefinition,
    AmazonProductType,
)
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonDefaultUnitConfigurator,
)
from sales_channels.integrations.amazon.models import AmazonCurrency
from eancodes.models import EanCode
from sales_prices.models import SalesPrice
from currencies.models import Currency
from currencies.currencies import currencies
from products.models import (
    ProductTranslation,
    ProductTranslationBulletPoint,
)
from media.models import Media, MediaProductThrough
from properties.models import (
    Property,
    PropertyTranslation,
    ProductProperty,
    ProductPropertyTextTranslation,
    ProductPropertiesRule,
    ProductPropertiesRuleItem,
    PropertySelectValue,
    PropertySelectValueTranslation,
)
from sales_channels.integrations.amazon.factories.products import (
    AmazonProductCreateFactory,
    AmazonProductUpdateFactory,
)
from sales_channels.integrations.amazon.factories.products.images import (
    AmazonMediaProductThroughBase,
)


class AmazonProductFactoriesTest(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER123",
            listing_owner=True
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="UK",
            api_region_code="EU_UK",
            remote_id="GB",
        )
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_code="en",
        )
        self.product = baker.make(
            "products.Product",
            sku="TESTSKU",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product_type_property = Property.objects.filter(is_product_type=True, multi_tenant_company=self.multi_tenant_company).first()

        self.product_type_value = baker.make(
            PropertySelectValue,
            property=self.product_type_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.product_type_value,
            language=self.multi_tenant_company.language,
            value="Chair",
        )

        self.rule = ProductPropertiesRule.objects.filter(
            product_type=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        ).first()
        ProductProperty.objects.create(
            product=self.product,
            property=self.product_type_property,
            value_select=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        # create asin property and assign to product so factories can fetch it
        asin_local = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
            internal_name="merchant_suggested_asin",
            non_deletable=True,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=asin_local,
            language=self.multi_tenant_company.language,
            name="Amazon Asin",
        )
        pp = ProductProperty.objects.create(
            product=self.product,
            property=asin_local,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertyTextTranslation.objects.create(
            product_property=pp,
            language=self.multi_tenant_company.language,
            value_text="ASIN123",
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=asin_local,
            code="merchant_suggested_asin",
            type=Property.TYPES.TEXT,
        )
        self.remote_product = AmazonProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="AMZSKU",
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel_view=self.view,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )

        # currency and price
        self.currency = Currency.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            is_default_currency=True,
            **currencies["GB"],
        )
        AmazonCurrency.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            local_instance=self.currency,
            remote_code=self.currency.iso_code,
        )
        SalesPrice.objects.create(
            product=self.product,
            currency=self.currency,
            rrp=100,
            price=80,
            multi_tenant_company=self.multi_tenant_company,
        )

        # content
        translation = ProductTranslation.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            language=self.multi_tenant_company.language,
            name="Chair name",
            description="Chair description",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslationBulletPoint.objects.create(
            product_translation=translation,
            multi_tenant_company=self.multi_tenant_company,
            text="First bullet",
            sort_order=0,
        )

        # image
        media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.IMAGE,
            owner=self.user,
        )
        MediaProductThrough.objects.create(
            product=self.product,
            media=media,
            sort_order=0,
            multi_tenant_company=self.multi_tenant_company,
        )

        # product type and remote type
        AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.rule,
            product_type_code="CHAIR",
        )

        AmazonDefaultUnitConfigurator.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            name="Item Package Weight Unit",
            code="item_package_weight",
            selected_unit="grams",
        )
        AmazonDefaultUnitConfigurator.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            name="Battery Weight Unit",
            code="battery__weight",
            selected_unit="grams",
        )

        # color property
        self.color_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            internal_name="color",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.color_property,
            language=self.multi_tenant_company.language,
            name="Color",
        )
        color_value = baker.make(
            PropertySelectValue,
            property=self.color_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=color_value,
            language=self.multi_tenant_company.language,
            value="Red",
        )
        ProductProperty.objects.create(
            product=self.product,
            property=self.color_property,
            value_select=color_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.color_property,
            code="color",
            type=Property.TYPES.SELECT,
            allows_unmapped_values=True,
        )

        # battery properties
        self.battery_cell = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            internal_name="battery__cell_composition",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.battery_cell,
            language=self.multi_tenant_company.language,
            name="Battery Cell Composition",
        )
        cell_value = baker.make(
            PropertySelectValue,
            property=self.battery_cell,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=cell_value,
            language=self.multi_tenant_company.language,
            value="lithium_ion",
        )
        ProductProperty.objects.create(
            product=self.product,
            property=self.battery_cell,
            value_select=cell_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.battery_cell,
            code="battery__cell_composition",
            type=Property.TYPES.SELECT,
            allows_unmapped_values=True,
        )

        self.battery_iec = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            internal_name="battery__iec_code",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.battery_iec,
            language=self.multi_tenant_company.language,
            name="Battery IEC Code",
        )
        iec_value = baker.make(
            PropertySelectValue,
            property=self.battery_iec,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=iec_value,
            language=self.multi_tenant_company.language,
            value="18650",
        )
        ProductProperty.objects.create(
            product=self.product,
            property=self.battery_iec,
            value_select=iec_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.battery_iec,
            code="battery__iec_code",
            type=Property.TYPES.SELECT,
            allows_unmapped_values=True,
        )

        self.battery_weight = baker.make(
            Property,
            type=Property.TYPES.FLOAT,
            internal_name="battery__weight",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.battery_weight,
            language=self.multi_tenant_company.language,
            name="Battery Weight",
        )
        ProductProperty.objects.create(
            product=self.product,
            property=self.battery_weight,
            value_float=10.0,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.battery_weight,
            code="battery__weight",
            type=Property.TYPES.FLOAT,
        )

        # batteries required
        self.batteries_required = baker.make(
            Property,
            type=Property.TYPES.BOOLEAN,
            internal_name="batteries_required",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.batteries_required,
            language=self.multi_tenant_company.language,
            name="Batteries Required",
        )
        ProductProperty.objects.create(
            product=self.product,
            property=self.batteries_required,
            value_boolean=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.batteries_required,
            code="batteries_required",
            type=Property.TYPES.BOOLEAN,
        )

        # condition type
        self.condition_type = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            internal_name="condition_type",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.condition_type,
            language=self.multi_tenant_company.language,
            name="Condition Type",
        )
        cond_value = baker.make(
            PropertySelectValue,
            property=self.condition_type,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=cond_value,
            language=self.multi_tenant_company.language,
            value="new",
        )
        ProductProperty.objects.create(
            product=self.product,
            property=self.condition_type,
            value_select=cond_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.condition_type,
            code="condition_type",
            type=Property.TYPES.SELECT,
            allows_unmapped_values=True,
        )

        # item package weight
        self.item_weight = baker.make(
            Property,
            type=Property.TYPES.FLOAT,
            internal_name="item_package_weight",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.item_weight,
            language=self.multi_tenant_company.language,
            name="Item Package Weight",
        )
        ProductProperty.objects.create(
            product=self.product,
            property=self.item_weight,
            value_float=2.5,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.item_weight,
            code="item_package_weight",
            type=Property.TYPES.FLOAT,
        )

        # rule items
        for prop in [
            self.color_property,
            self.battery_cell,
            self.battery_iec,
            self.battery_weight,
            self.batteries_required,
            self.condition_type,
            self.item_weight,
        ]:
            ProductPropertiesRuleItem.objects.get_or_create(
                multi_tenant_company=self.multi_tenant_company,
                rule=self.rule,
                property=prop,
                defaults={"type": ProductPropertiesRuleItem.OPTIONAL},
            )

        # public definitions
        AmazonPublicDefinition.objects.create(
            api_region_code="EU_UK",
            product_type_code="CHAIR",
            code="color",
            name="Color",
            usage_definition=json.dumps(
                {
                    "color": [
                        {
                            "standardized_values": ["%value:color%"],
                            "value": "%value:color%",
                            "language_tag": "%auto:language%",
                            "marketplace_id": "%auto:marketplace_id%",
                        }
                    ]
                }
            ),
        )
        AmazonPublicDefinition.objects.create(
            api_region_code="EU_UK",
            product_type_code="CHAIR",
            code="battery",
            name="Battery",
            usage_definition=json.dumps(
                {
                    "battery": [
                        {
                            "cell_composition": [
                                {"value": "%value:battery__cell_composition%"}
                            ],
                            "cell_composition_other_than_listed": [
                                {
                                    "value": "%value:battery__cell_composition%",
                                    "language_tag": "%auto:language%",
                                }
                            ],
                            "iec_code": [
                                {"value": "%value:battery__iec_code%"}
                            ],
                            "weight": [
                                {
                                    "value": "%value:battery__weight%",
                                    "unit": "%unit:battery__weight%",
                                }
                            ],
                            "marketplace_id": "%auto:marketplace_id%",
                        }
                    ]
                }
            ),
        )
        AmazonPublicDefinition.objects.create(
            api_region_code="EU_UK",
            product_type_code="CHAIR",
            code="batteries_required",
            name="Batteries Required",
            usage_definition=json.dumps(
                {
                    "batteries_required": [
                        {
                            "value": "%value:batteries_required%",
                            "marketplace_id": "%auto:marketplace_id%",
                        }
                    ]
                }
            ),
        )
        AmazonPublicDefinition.objects.create(
            api_region_code="EU_UK",
            product_type_code="CHAIR",
            code="condition_type",
            name="Condition Type",
            usage_definition=json.dumps(
                {
                    "condition_type": [
                        {
                            "value": "%value:condition_type%",
                            "marketplace_id": "%auto:marketplace_id%",
                        }
                    ]
                }
            ),
        )
        AmazonPublicDefinition.objects.create(
            api_region_code="EU_UK",
            product_type_code="CHAIR",
            code="item_package_weight",
            name="Item Package Weight",
            usage_definition=json.dumps(
                {
                    "item_package_weight": [
                        {
                            "value": "%value:item_package_weight%",
                            "unit": "%unit:item_package_weight%",
                            "marketplace_id": "%auto:marketplace_id%",
                        }
                    ]
                }
            ),
        )

    def get_put_and_patch_item_listing_mock_response(self, attributes=None):
        mock_response = MagicMock(spec=["submissionId", "processingStatus", "issues", "status"])
        mock_response.submissionId = "mock-submission-id"
        mock_response.processingStatus = "VALID"
        mock_response.status = "VALID"
        mock_response.issues = []

        if attributes:
            mock_response.attributes = attributes

        return mock_response

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_create_product_factory_builds_correct_body(self, mock_listings, mock_client):
        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.put_listings_item.call_args.kwargs.get("body")
        self.assertIsInstance(body, dict)
        self.assertEqual(body.get("requirements"), "LISTING")

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_update_product_factory_builds_correct_body(self, mock_listings, mock_get_client):
        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

        fac = AmazonProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.put_listings_item.call_args.kwargs.get("body")
        self.assertIsInstance(body, dict)
        self.assertEqual(body.get("requirements"), "LISTING")

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_create_product_factory_builds_correct_payload(self, mock_listings, mock_get_images, mock_get_client):
        """This test checks if the CreateFactory gives the expected payload including attributes, prices, and content."""
        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

        url = 'https://example.com/img.jpg'

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.put_listings_item.call_args.kwargs.get("body")

        keys = list(AmazonMediaProductThroughBase.OFFER_KEYS) + list(AmazonMediaProductThroughBase.PRODUCT_KEYS)
        expected_images = {
            key: [{"media_location": url}]
            for key in keys
            if key in ("main_offer_image_locator", "main_product_image_locator")
        }

        expected_attributes = {
            "merchant_suggested_asin": "ASIN123",
            "item_name": "Chair name",
            "product_description": "Chair description",
            "bullet_point": ["First bullet"],
            "list_price": [{"currency": "GBP", "amount": 80.0}],
            "uvp_list_price": [{"currency": "GBP", "amount": 100.0}],
            **expected_images,
            "color": [
                {
                    "standardized_values": ["Red"],
                    "value": "Red",
                    "language_tag": "en",
                    "marketplace_id": "GB",
                }
            ],
            "battery": [
                {
                    "cell_composition": [{"value": "lithium_ion"}],
                    "cell_composition_other_than_listed": [
                        {"value": "lithium_ion", "language_tag": "en"}
                    ],
                    "iec_code": [{"value": "18650"}],
                    "weight": [{"value": 10.0, "unit": "grams"}],
                    "marketplace_id": "GB",
                }
            ],
            "batteries_required": [
                {"value": True, "marketplace_id": "GB"}
            ],
            "condition_type": [
                {"value": "new", "marketplace_id": "GB"}
            ],
            "item_package_weight": [
                {"value": 2.5, "unit": "grams", "marketplace_id": "GB"}
            ],
        }

        expected_body = {
            "productType": "PRODUCT",
            "requirements": "LISTING",
            "attributes": expected_attributes,
        }

        self.assertEqual(body, expected_body)

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_update_product_factory_builds_correct_payload(self, mock_listings, mock_get_images, mock_get_client):
        """This test checks that the update factory builds a correct patch payload with only changed attributes."""
        url = "https://example.com/img.jpg"

        # mark product as already created on this marketplace so update runs
        self.remote_product.created_marketplaces = [self.view.remote_id]
        self.remote_product.save()

        current_attrs = {
            "item_name": "Old name",
        }

        mock_instance = mock_listings.return_value
        mock_instance.patch_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

        current_attrs = {"item_name": "Old name"}
        mock_instance.get_listings_item.return_value = SimpleNamespace(attributes=current_attrs)

        fac = AmazonProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")
        expected_patches = fac._build_patches(current_attrs, fac.payload["attributes"])
        expected_body = {
            "productType": "PRODUCT",
            "patches": expected_patches,
        }

        self.assertEqual(body, expected_body)

    @patch(
        "sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client",
        return_value=None,
    )
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    @patch(
        "sales_channels.integrations.amazon.factories.products.AmazonProductCreateFactory.run",
        wraps=AmazonProductCreateFactory.run,
        autospec=True
    )
    def test_sync_switches_to_create_if_product_not_exists(
        self, mock_create_run, mock_listings, mock_get_client
    ):
        """This test ensures that calling sync triggers a create if the product doesn't exist remotely."""
        self.remote_product.created_marketplaces = []
        self.remote_product.save()

        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = (
            self.get_put_and_patch_item_listing_mock_response()
        )

        fac = AmazonProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )

        fac.run()

        mock_create_run.assert_called_once()
        mock_instance.put_listings_item.assert_called()
        mock_instance.patch_listings_item.assert_not_called()

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_create_product_on_different_marketplace(self, mock_listings, mock_get_images, mock_get_client):
        """This test ensures the product is created on a second marketplace correctly and independently using PUT."""
        fr_view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="France",
            api_region_code=self.view.api_region_code,
            remote_id="FR",
        )
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=fr_view,
            remote_code="fr",
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel_view=fr_view,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )
        AmazonCurrency.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=fr_view,
            local_instance=self.currency,
            remote_code=self.currency.iso_code,
        )
        AmazonDefaultUnitConfigurator.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=fr_view,
            name="Item Package Weight Unit",
            code="item_package_weight",
            selected_unit="grams",
        )
        AmazonDefaultUnitConfigurator.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=fr_view,
            name="Battery Weight Unit",
            code="battery__weight",
            selected_unit="grams",
        )

        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=fr_view,
        )
        fac.run()

        mock_instance.put_listings_item.assert_called_once()
        mock_instance.patch_listings_item.assert_not_called()

        kwargs = mock_instance.put_listings_item.call_args.kwargs
        self.assertEqual(kwargs.get("marketplace_ids"), ["FR"])

        body = kwargs.get("body")
        keys = list(AmazonMediaProductThroughBase.OFFER_KEYS) + list(AmazonMediaProductThroughBase.PRODUCT_KEYS)
        expected_images = {
            key: [{"media_location": "https://example.com/img.jpg"}]
            for key in keys
            if key in ("main_offer_image_locator", "main_product_image_locator")
        }
        expected_attributes = {
            "merchant_suggested_asin": "ASIN123",
            "item_name": "Chair name",
            "product_description": "Chair description",
            "bullet_point": ["First bullet"],
            "list_price": [{"currency": "GBP", "amount": 80.0}],
            "uvp_list_price": [{"currency": "GBP", "amount": 100.0}],
            **expected_images,
            "color": [
                {
                    "standardized_values": ["Red"],
                    "value": "Red",
                    "language_tag": "fr",
                    "marketplace_id": "FR",
                }
            ],
            "battery": [
                {
                    "cell_composition": [{"value": "lithium_ion"}],
                    "cell_composition_other_than_listed": [
                        {"value": "lithium_ion", "language_tag": "fr"}
                    ],
                    "iec_code": [{"value": "18650"}],
                    "weight": [{"value": 10.0, "unit": "grams"}],
                    "marketplace_id": "FR",
                }
            ],
            "batteries_required": [
                {"value": True, "marketplace_id": "FR"}
            ],
            "condition_type": [
                {"value": "new", "marketplace_id": "FR"}
            ],
            "item_package_weight": [
                {"value": 2.5, "unit": "grams", "marketplace_id": "FR"}
            ],
        }
        expected_body = {
            "productType": "PRODUCT",
            "requirements": "LISTING",
            "attributes": expected_attributes,
        }

        self.assertEqual(body, expected_body)

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch("sales_channels.integrations.amazon.factories.products.products.ListingsApi")
    def test_delete_product_uses_correct_sku_and_marketplace(self, mock_listings, mock_client):
        """This test ensures delete factory calls the correct endpoint with the proper SKU and marketplace ID."""
        mock_instance = mock_listings.return_value
        mock_instance.delete_listings_item.return_value = {"status": "deleted"}

        fac = AmazonProductDeleteFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        mock_instance.delete_listings_item.assert_called_once()
        kwargs = mock_instance.delete_listings_item.call_args.kwargs
        self.assertEqual(kwargs.get("sku"), self.remote_product.remote_sku)
        self.assertEqual(kwargs.get("marketplace_ids"), [self.view.remote_id])

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch("sales_channels.integrations.amazon.factories.products.AmazonProductCreateFactory.run")
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_update_falls_back_to_create_if_product_missing_remotely(
        self, mock_listings, mock_create_run, mock_get_client
    ):
        """This test ensures update falls back to create if the product doesn’t exist remotely in the given marketplace."""
        self.remote_product.created_marketplaces = [self.view.remote_id]
        self.remote_product.save()

        mock_instance = mock_listings.return_value
        mock_instance.get_listings_item.side_effect = Exception("Not found")

        # Prevent accidental logging crash (mocking even if it shouldn't be called)
        mock_instance.patch_listings_item.return_value = {
            "submissionId": "mock-submission-id",
            "processingStatus": "VALID",
            "status": "VALID",
            "issues": [],
        }

        fac = AmazonProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        mock_instance.patch_listings_item.assert_not_called()
        mock_create_run.assert_called_once()

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img-new.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_update_images_overwrites_old_ones_correctly(self, mock_listings, mock_get_images, mock_get_client):
        """This test validates that old images are removed and only the new ones are included in the payload."""
        self.remote_product.created_marketplaces = [self.view.remote_id]
        self.remote_product.save()

        mock_instance = mock_listings.return_value
        mock_instance.get_listings_item.return_value = SimpleNamespace(
            attributes={
                "main_product_image_locator": [
                    {"media_location": "https://example.com/img-old.jpg"}
                ]
            }
        )
        mock_instance.patch_listings_item.return_value = (
            self.get_put_and_patch_item_listing_mock_response()
        )

        fac = AmazonProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")
        patches = body.get("patches", [])
        patch_for_main = next(
            (
                p
                for p in patches
                if "main_product_image_locator" in p.get("value", [{}])[0]
            ),
            None,
        )

        self.assertIsNotNone(patch_for_main)
        self.assertEqual(patch_for_main["op"], "replace")
        self.assertEqual(
            patch_for_main["value"][0]["main_product_image_locator"][0][
                "media_location"
            ],
            "https://example.com/img-new.jpg",
        )
        mock_instance.patch_listings_item.assert_called_once()

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_payload_includes_all_supported_property_types(self, mock_listings, mock_get_images, mock_get_client):
        """This test adds text, select, and multiselect properties and confirms their correct payload structure."""
        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

        # TEXT property
        text_prop = baker.make(
            Property,
            type=Property.TYPES.TEXT,
            internal_name="notes",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=text_prop,
            language=self.multi_tenant_company.language,
            name="Notes",
        )
        pp_text = ProductProperty.objects.create(
            product=self.product,
            property=text_prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertyTextTranslation.objects.create(
            product_property=pp_text,
            language=self.multi_tenant_company.language,
            value_text="Some text",
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=text_prop,
            code="notes",
            type=Property.TYPES.TEXT,
        )
        AmazonPublicDefinition.objects.create(
            api_region_code="EU_UK",
            product_type_code="CHAIR",
            code="notes",
            name="Notes",
            usage_definition=json.dumps(
                {
                    "notes": [
                        {"value": "%value:notes%", "marketplace_id": "%auto:marketplace_id%"}
                    ]
                }
            ),
        )

        # SELECT property
        select_prop = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            internal_name="material",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=select_prop,
            language=self.multi_tenant_company.language,
            name="Material",
        )
        select_val = baker.make(
            PropertySelectValue,
            property=select_prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=select_val,
            language=self.multi_tenant_company.language,
            value="Green",
        )
        ProductProperty.objects.create(
            product=self.product,
            property=select_prop,
            value_select=select_val,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=select_prop,
            code="material",
            type=Property.TYPES.SELECT,
            allows_unmapped_values=True,
        )
        AmazonPublicDefinition.objects.create(
            api_region_code="EU_UK",
            product_type_code="CHAIR",
            code="material",
            name="Material",
            usage_definition=json.dumps(
                {
                    "material": [
                        {"value": "%value:material%", "marketplace_id": "%auto:marketplace_id%"}
                    ]
                }
            ),
        )

        # MULTISELECT property
        multi_prop = baker.make(
            Property,
            type=Property.TYPES.MULTISELECT,
            internal_name="size",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=multi_prop,
            language=self.multi_tenant_company.language,
            name="Size",
        )
        size_val1 = baker.make(
            PropertySelectValue,
            property=multi_prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        size_val2 = baker.make(
            PropertySelectValue,
            property=multi_prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=size_val1,
            language=self.multi_tenant_company.language,
            value="Small",
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=size_val2,
            language=self.multi_tenant_company.language,
            value="Large",
        )
        pp_multi = ProductProperty.objects.create(
            product=self.product,
            property=multi_prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        pp_multi.value_multi_select.set([size_val1, size_val2])
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=multi_prop,
            code="size",
            type=Property.TYPES.MULTISELECT,
            allows_unmapped_values=True,
        )
        AmazonPublicDefinition.objects.create(
            api_region_code="EU_UK",
            product_type_code="CHAIR",
            code="size",
            name="Size",
            usage_definition=json.dumps(
                {
                    "size": [
                        {"value": "%value:size%", "marketplace_id": "%auto:marketplace_id%"}
                    ]
                }
            ),
        )

        for prop in [text_prop, select_prop, multi_prop]:
            ProductPropertiesRuleItem.objects.get_or_create(
                multi_tenant_company=self.multi_tenant_company,
                rule=self.rule,
                property=prop,
                defaults={"type": ProductPropertiesRuleItem.OPTIONAL},
            )

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.put_listings_item.call_args.kwargs.get("body")
        attrs = body.get("attributes")

        self.assertEqual(
            attrs.get("notes"),
            [{"value": "Some text", "marketplace_id": "GB"}],
        )
        self.assertEqual(
            attrs.get("material"),
            [{"value": "Green", "marketplace_id": "GB"}],
        )
        self.assertEqual(
            attrs.get("size"),
            [{"value": ["Large", "Small"], "marketplace_id": "GB"}],
        )

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_unmapped_attributes_are_ignored_in_payload(self, mock_listings, mock_get_images, mock_get_client):
        """This test confirms that unmapped or unknown attributes are not added to the final payload."""
        fake_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            internal_name="fake_property",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=fake_property,
            language=self.multi_tenant_company.language,
            name="Fake Property",
        )
        fake_value = baker.make(
            PropertySelectValue,
            property=fake_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=fake_value,
            language=self.multi_tenant_company.language,
            value="Fake",
        )
        ProductProperty.objects.create(
            product=self.product,
            property=fake_property,
            value_select=fake_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = (
            self.get_put_and_patch_item_listing_mock_response()
        )

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.put_listings_item.call_args.kwargs.get("body")
        self.assertNotIn("fake_property", body.get("attributes", {}))

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_missing_ean_or_asin_raises_exception(self, mock_listings, mock_get_client):
        """This test ensures the factory raises ValueError if no EAN/GTIN or ASIN is provided."""
        ProductProperty.objects.filter(
            product=self.product,
            property__internal_name="merchant_suggested_asin",
        ).delete()
        AmazonProperty.objects.filter(
            sales_channel=self.sales_channel,
            code="merchant_suggested_asin",
        ).delete()

        EanCode.objects.filter(product=self.product).delete()
        self.remote_product.ean_code = None
        self.remote_product.save()

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )

        with self.assertRaises(ValueError) as ctx:
            fac.run()

        self.assertIn("ASIN or EAN", str(ctx.exception))
        mock_listings.return_value.put_listings_item.assert_not_called()

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_create_product_with_asin_in_payload(self, mock_listings, mock_get_images, mock_get_client):
        """This test confirms that ASIN is correctly added and EAN is skipped if ASIN exists."""
        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = (
            self.get_put_and_patch_item_listing_mock_response()
        )

        self.remote_product.ean_code = None

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.put_listings_item.call_args.kwargs.get("body")
        attrs = body.get("attributes", {})

        self.assertEqual(attrs.get("merchant_suggested_asin"), "ASIN123")
        self.assertNotIn("external_product_id", attrs)
        self.assertNotIn("external_product_id_type", attrs)

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_create_product_with_ean_in_payload(self, mock_listings, mock_get_images, mock_get_client):
        """This test verifies that EAN is included properly in the absence of ASIN."""
        asin_property = Property.objects.get(
            internal_name="merchant_suggested_asin",
            multi_tenant_company=self.multi_tenant_company,
        )

        ProductProperty.objects.filter(
            product=self.product,
            property=asin_property,
        ).delete()

        AmazonProperty.objects.filter(
            local_instance=asin_property,
            sales_channel=self.sales_channel,
        ).delete()

        EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            ean_code="1234567890123",
        )

        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.put_listings_item.call_args.kwargs.get("body")
        attrs = body.get("attributes", {})

        self.assertEqual(attrs.get("external_product_id"), "1234567890123")
        self.assertEqual(attrs.get("external_product_id_type"), "EAN")
        self.assertNotIn("merchant_suggested_asin", attrs)

    def test_existing_remote_property_gets_updated(self):
        """This test simulates an existing remote property and checks that update payload reflects correct values."""
        pass

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_translation_from_sales_channel_is_used_in_payload(
        self, mock_listings, mock_get_images, mock_get_client
    ):
        """This test checks that product content is pulled from sales channel translations if available."""

        baker.make(
            ProductTranslation,
            product=self.product,
            sales_channel=None,
            language=self.multi_tenant_company.language,
            name="Global Name",
            description="Global Description",
            multi_tenant_company=self.multi_tenant_company,
        )

        translation = ProductTranslation.objects.get(
            product=self.product,
            sales_channel=self.sales_channel,
            language=self.multi_tenant_company.language,
        )
        translation.name = "Channel Name"
        translation.description = "Channel Description"
        translation.save()

        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = (
            self.get_put_and_patch_item_listing_mock_response()
        )

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.put_listings_item.call_args.kwargs.get("body")
        attrs = body.get("attributes", {})
        self.assertEqual(attrs.get("item_name"), "Channel Name")
        self.assertEqual(attrs.get("product_description"), "Channel Description")

    def test_translation_fallbacks_to_global_if_not_in_channel(self):
        """This test ensures fallback to global translation when channel-specific translation is missing."""
        pass

    def test_price_sync_enabled_includes_price_fields(self):
        """This test ensures that enabling price sync includes correct pricing fields like list_price and uvp_list_price."""
        pass

    def test_price_sync_disabled_skips_price_fields(self):
        """This test ensures that price fields are skipped when price sync is turned off."""
        pass

    def test_payload_skips_empty_price_fields_gracefully(self):
        """This test confirms that missing prices do not break payload generation and are omitted silently."""
        pass

    def test_missing_view_argument_raises_value_error(self):
        """This test confirms that initializing a factory without a view raises ValueError."""
        pass
