from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from django.templatetags.i18n import language
from django.test import override_settings
import json

from model_bakery import baker

from core.tests import TestCase
from core.tests import TransactionTestCase
from sales_channels.integrations.amazon.factories import AmazonProductDeleteFactory, AmazonProductSyncFactory
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.factories.properties.mixins import (
    AmazonProductPropertyBaseMixin,
)
from sales_channels.integrations.amazon.tests.helpers import DisableWooCommerceSignalsMixin

from sales_channels.models.sales_channels import SalesChannelViewAssign
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonRemoteLanguage,
)
from sales_channels.integrations.amazon.models.products import (
    AmazonProduct,
    AmazonExternalProductId,
    AmazonGtinExemption,
    AmazonVariationTheme,
)
from sales_channels.integrations.amazon.models.properties import (
    AmazonProperty,
    AmazonPublicDefinition,
    AmazonProductType,
)
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonDefaultUnitConfigurator,
)
from sales_channels.integrations.amazon.models import AmazonCurrency
from sales_channels.integrations.amazon.models.recommended_browse_nodes import (
    AmazonProductBrowseNode,
)
from sales_channels.integrations.amazon.models import AmazonCurrency, AmazonProductBrowseNode
from eancodes.models import EanCode
from sales_prices.models import SalesPrice
from currencies.models import Currency
from currencies.currencies import currencies
from products.models import (
    ProductTranslation,
    ProductTranslationBulletPoint, Product,
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
from sales_channels.integrations.amazon.factories.products.products import (
    AmazonProductBaseFactory,
)
from sales_channels.integrations.amazon.factories.products.images import (
    AmazonMediaProductThroughBase,
)
from sales_channels.models.products import RemoteProductConfigurator
from products.models import ConfigurableVariation


class AmazonProductTestMixin:
    def setup_product(self):
        """Create common data used by Amazon product factory tests."""
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER123",
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
            local_instance="en"
        )
        self.product = baker.make(
            "products.Product",
            sku="TESTSKU",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product_type_property = Property.objects.filter(
            is_product_type=True,
            multi_tenant_company=self.multi_tenant_company,
        ).first()

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
        self.remote_product = AmazonProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="TESTSKU",
        )
        self.remote_product.product_owner = True
        self.remote_product.save()

        AmazonExternalProductId.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            view=self.view,
            value="ASIN123",
        )
        AmazonProductBrowseNode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel=self.sales_channel,
            view=self.view,
            recommended_browse_node_id="1",
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel_view=self.view,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )

        self.currency, _ = Currency.objects.get_or_create(
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
            price=80,
            multi_tenant_company=self.multi_tenant_company,
        )

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

    def get_get_listing_item_mock_response(self, attributes=None):
        """Helper to mock the ListingsApi.get_listings_item response."""
        return SimpleNamespace(attributes=attributes or {})

    def get_patch_value(self, patches, path):
        for patch in patches:
            if patch["path"] == path:
                return patch["value"]
        return None


class AmazonProductFactoriesTest(DisableWooCommerceSignalsMixin, TransactionTestCase, AmazonProductTestMixin):
    def setUp(self):
        super().setUp()
        self.setup_product()

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_create_product_factory_builds_correct_body(self, mock_listings, mock_client):
        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

        # to be LISTING this needs to not have any ASIN on create
        AmazonExternalProductId.objects.filter(type=AmazonExternalProductId.TYPE_ASIN).delete()
        EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            ean_code="1234567890123",
        )

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
        mock_instance.patch_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()
        self.remote_product.created_marketplaces = ['GB']

        fac = AmazonProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")
        self.assertIsInstance(body, dict)

    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_update_product_skips_when_no_patches(self, mock_listings):
        class Dummy(GetAmazonAPIMixin):
            def __init__(self, sales_channel, view):
                self.sales_channel = sales_channel
                self.view = view

            def _get_client(self):
                return None

            def get_identifiers(self):
                return "test", "test"

            def update_assign_issues(self, *args, **kwargs):
                pass

        dummy = Dummy(self.sales_channel, self.view)

        product_type = AmazonProductType.objects.get(local_instance=self.rule)
        with patch.object(dummy, "_build_patches", return_value=[]):
            response = dummy.update_product(
                "AMZSKU",
                self.view.remote_id,
                product_type,
                {"item_name": []},
                current_attributes={"item_name": []},
            )

        mock_listings.return_value.patch_listings_item.assert_not_called()
        self.assertIsNone(response)

    def test_build_patches_adds_value_for_delete(self):
        mixin = GetAmazonAPIMixin()
        current = {
            "other_product_image_locator_1": [
                {"marketplace_id": "GB", "media_location": "https://example.com/img.jpg"}
            ]
        }
        new = {"other_product_image_locator_1": None}
        patches = mixin._build_patches(current, new)
        expected = {
            "op": "delete",
            "path": "/attributes/other_product_image_locator_1",
            "value": current["other_product_image_locator_1"],
        }
        self.assertIn(expected, patches)

    def test_build_patches_keeps_non_all_audiences(self):
        mixin = GetAmazonAPIMixin()
        current = {
            "purchasable_offer": [
                {"audience": "ALL", "currency": "GBP"},
                {"audience": "B2B", "currency": "GBP"},
            ]
        }
        new = {
            "purchasable_offer": [
                {"audience": "ALL", "currency": "GBP"}
            ]
        }
        patches = mixin._build_patches(current, new)
        self.assertEqual(patches, [])

    def test_build_patches_ignores_marketplace_id(self):
        mixin = GetAmazonAPIMixin()
        current = {"attr": [{"marketplace_id": "GB", "value": "foo"}]}
        new = {"attr": [{"value": "foo"}]}
        self.assertEqual(mixin._build_patches(current, new), [])
        self.assertEqual(
            mixin._build_patches({"attr": [{"value": "foo"}]}, {"attr": [{"marketplace_id": "GB", "value": "foo"}]}),
            [],
        )

    def test_replace_tokens_drops_empty_units(self):
        mixin = AmazonProductPropertyBaseMixin()
        data = {
            "battery": [
                {
                    "marketplace_id": "A1F83G8C2ARO7P",
                    "weight": [{"unit": "grams", "value": None}],
                }
            ]
        }
        cleaned = mixin._replace_tokens(data, None)
        self.assertEqual(cleaned, {})

    @override_settings(DEBUG=False)
    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_create_product_factory_forces_validation_mode(self, mock_listings, mock_client):
        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
            force_validation_only=True,
        )
        fac.run()

        self.assertEqual(
            mock_instance.put_listings_item.call_args.kwargs.get("mode"),
            "VALIDATION_PREVIEW",
        )

    @override_settings(DEBUG=False)
    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_update_product_factory_forces_validation_mode(self, mock_listings, mock_client):
        mock_instance = mock_listings.return_value
        mock_instance.patch_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()
        mock_instance.get_listings_item.return_value = SimpleNamespace(attributes={})
        self.remote_product.created_marketplaces = ['GB']
        self.remote_product.save()

        fac = AmazonProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
            force_validation_only=True,
        )
        fac.run()

        self.assertEqual(
            mock_instance.patch_listings_item.call_args.kwargs.get("mode"),
            "VALIDATION_PREVIEW",
        )

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_sync_factory_uses_create_when_force_full_update(
        self,
        mock_listings,
        mock_get_images,
        mock_get_client,
    ):
        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

        self.remote_product.created_marketplaces = [self.view.remote_id]
        self.remote_product.save(update_fields=["created_marketplaces"])

        fac = AmazonProductSyncFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
            force_full_update=True,
        )
        fac.run()

        mock_instance.put_listings_item.assert_called_once()
        mock_instance.patch_listings_item.assert_not_called()

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_create_product_factory_builds_correct_payload(self, mock_listings, mock_get_images, mock_get_client):
        """This test checks if the CreateFactory gives the expected payload including attributes, prices, and content."""
        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()
        AmazonExternalProductId.objects.filter(type=AmazonExternalProductId.TYPE_ASIN).delete()
        EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            ean_code="1234567890123",
        )

        url = 'https://example.com/img.jpg'

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.put_listings_item.call_args.kwargs.get("body")

        # keys = (
        #     list(AmazonMediaProductThroughBase.OFFER_KEYS)
        #     + list(AmazonMediaProductThroughBase.PRODUCT_KEYS)
        # )
        keys = list(AmazonMediaProductThroughBase.PRODUCT_KEYS)

        expected_images = {
            key: [{"marketplace_id": "GB", "media_location": url}]
            for key in keys
            if key in ("main_offer_image_locator", "main_product_image_locator")
        }

        expected_attributes = {
            "externally_assigned_product_identifier": [
                {"type": "ean", "value": "1234567890123", "marketplace_id": "GB"}
            ],
            "item_name": [
                {
                    "value": "Chair name",
                    "language_tag": "en",
                    "marketplace_id": "GB",
                }
            ],
            "product_description": [
                {
                    "value": "Chair description",
                    "language_tag": "en",
                    "marketplace_id": "GB",
                }
            ],
            "bullet_point": [
                {
                    "value": "First bullet",
                    "language_tag": "en",
                    "marketplace_id": "GB",
                }
            ],
            "purchasable_offer": [
                {
                    "audience": "ALL",
                    "currency": "GBP",
                    "marketplace_id": "GB",
                    "our_price": [
                        {"schedule": [{"value_with_tax": 80.0}]}
                    ],
                }
            ],
            "list_price": [{"currency": "GBP", "value_with_tax": 80.0}],
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
                    "iec_code": [{"value": 18650}],
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
            "recommended_browse_nodes": [{'marketplace_id': 'GB', 'value': 1}]
        }

        expected_body = {
            "productType": "CHAIR",
            "requirements": "LISTING",
            "attributes": expected_attributes,
        }

        self.assertEqual(body, expected_body)

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_update_product_factory_builds_correct_payload(self, mock_listings, mock_get_images, mock_get_client):
        """This test checks that the update factory builds a correct payload using PATCH."""
        url = "https://example.com/img.jpg"

        # mark product as already created on this marketplace so update runs
        self.remote_product.created_marketplaces = [self.view.remote_id]
        self.remote_product.save()

        mock_instance = mock_listings.return_value
        mock_instance.patch_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

        current_attrs = {
            "item_name": [
                {
                    "value": "Old name",
                    "language_tag": "en",
                    "marketplace_id": "GB",
                }
            ]
        }
        mock_instance.get_listings_item.return_value = SimpleNamespace(attributes=current_attrs)

        fac = AmazonProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")

        self.assertEqual(body["productType"], "CHAIR")
        self.assertIn(
            {
                "op": "replace",
                "path": "/attributes/item_name",
                "value": [{
                    "value": "Chair name",
                    "language_tag": "en",
                    "marketplace_id": "GB",
                }],
            },
            body["patches"]
        )

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_update_product_skips_merchant_asin_patch(self, mock_listings, mock_get_images, mock_get_client):
        """ASIN should never be part of the patch payload."""
        self.remote_product.created_marketplaces = [self.view.remote_id]
        self.remote_product.save()

        mock_instance = mock_listings.return_value
        mock_instance.patch_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()
        mock_instance.get_listings_item.return_value = SimpleNamespace(attributes={})

        fac = AmazonProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")
        paths = [p.get("path") for p in body.get("patches", [])]
        self.assertNotIn("/attributes/merchant_suggested_asin", paths)

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_update_product_skips_external_id_patch(self, mock_listings, mock_get_images, mock_get_client):
        """External identifiers like EAN should not be patched."""
        self.remote_product.created_marketplaces = [self.view.remote_id]
        self.remote_product.ean_code = "1234567890123"
        self.remote_product.save()

        AmazonExternalProductId.objects.filter(
            product=self.product,
            view=self.view,
        ).delete()
        EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            ean_code="1234567890123",
        )

        mock_instance = mock_listings.return_value
        mock_instance.patch_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()
        mock_instance.get_listings_item.return_value = SimpleNamespace(attributes={})

        fac = AmazonProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")
        paths = [p.get("path") for p in body.get("patches", [])]
        self.assertNotIn("/attributes/externally_assigned_product_identifier", paths)

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
        translation = ProductTranslation.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            language="fr",
            name="Chair name fr",
            description="Chair description fr",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslationBulletPoint.objects.create(
            product_translation=translation,
            multi_tenant_company=self.multi_tenant_company,
            text="First bullet fr",
            sort_order=0,
        )
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=fr_view,
            remote_code="fr",
            local_instance='fr'
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

        AmazonExternalProductId.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            view=fr_view,
            value="ASIN123",
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

        kwargs = mock_instance.put_listings_item.call_args.kwargs
        self.assertEqual(kwargs.get("marketplace_ids"), ["FR"])

        body = kwargs.get("body")
        # keys = (
        #     list(AmazonMediaProductThroughBase.OFFER_KEYS)
        #     + list(AmazonMediaProductThroughBase.PRODUCT_KEYS)
        # )
        keys = list(AmazonMediaProductThroughBase.PRODUCT_KEYS)

        expected_images = {
            key: [{"marketplace_id": "FR", "media_location": "https://example.com/img.jpg"}]
            for key in keys
            if key in ("main_product_image_locator")
        }
        expected_attributes = {
            "merchant_suggested_asin": [
                {"value": "ASIN123", "marketplace_id": "FR"}
            ],
            "item_name": [
                {
                    "value": "Chair name fr",
                    "language_tag": "fr",
                    "marketplace_id": "FR",
                }
            ],
            "product_description": [
                {
                    "value": "Chair description fr",
                    "language_tag": "fr",
                    "marketplace_id": "FR",
                }
            ],
            "bullet_point": [
                {
                    "value": "First bullet fr",
                    "language_tag": "fr",
                    "marketplace_id": "FR",
                }
            ],
            "purchasable_offer": [
                {
                    "audience": "ALL",
                    "currency": "GBP",
                    "marketplace_id": "FR",
                    "our_price": [
                        {"schedule": [{"value_with_tax": 80.0}]}
                    ],
                }
            ],
            'list_price': [{'currency': 'GBP', "marketplace_id": "FR", 'value_with_tax': 80.0}],
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
                    "iec_code": [{"value": 18650}],
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
            "productType": "CHAIR",
            "requirements": "LISTING_OFFER_ONLY",
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

        # @TODO: Temporary disable deletes
        # mock_instance.delete_listings_item.assert_called_once()
        # kwargs = mock_instance.delete_listings_item.call_args.kwargs
        # self.assertEqual(kwargs.get("sku"), self.remote_product.remote_sku)
        # self.assertEqual(kwargs.get("marketplace_ids"), [self.view.remote_id])

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

    # @TODO: Temporary remove unti image update is fixed after import
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
                    {
                        "marketplace_id": "GB",
                        "media_location": "https://example.com/img-old.jpg",
                    }
                ]
            }
        )
        mock_instance.patch_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()
        fac = AmazonProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")

        self.assertIn(
            {
                "op": "replace",
                "path": "/attributes/main_product_image_locator",
                "value": [
                    {
                        "marketplace_id": "GB",
                        "media_location": "https://example.com/img-new.jpg",
                    }
                ],
            },
            body["patches"]
        )

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
        mock_instance.patch_listings_item.return_value = (
            self.get_put_and_patch_item_listing_mock_response()
        )

        self.remote_product.created_marketplaces = ['GB']
        fac = AmazonProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")
        patches = body.get("patches", [])
        paths = [patch.get("path") for patch in patches]

        self.assertNotIn("/attributes/fake_property", paths)

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_missing_ean_or_asin_raises_exception(self, mock_listings, mock_get_client):
        """This test ensures the factory raises ValueError if no EAN/GTIN or ASIN is provided."""
        AmazonExternalProductId.objects.filter(
            product=self.product,
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

        self.assertIn("external product id or EAN", str(ctx.exception))
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

        self.assertEqual(
            attrs.get("merchant_suggested_asin"),
            [{"value": "ASIN123", "marketplace_id": self.view.remote_id}],
        )
        self.assertNotIn("externally_assigned_product_identifier", attrs)

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_create_product_with_ean_in_payload(self, mock_listings, mock_get_images, mock_get_client):
        """This test verifies that EAN is included properly in the absence of ASIN."""
        AmazonExternalProductId.objects.filter(
            product=self.product,
            view=self.view,
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

        self.assertEqual(
            attrs.get("externally_assigned_product_identifier"),
            [
                {
                    "type": "ean",
                    "value": "1234567890123",
                    "marketplace_id": self.view.remote_id,
                }
            ],
        )
        self.assertNotIn("merchant_suggested_asin", attrs)

    @patch(
        "sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client",
        return_value=None,
    )
    @patch.object(
        AmazonMediaProductThroughBase,
        "_get_images",
        return_value=["https://example.com/img.jpg"],
    )
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_create_product_with_gtin_exemption(self, mock_listings, mock_get_images, mock_get_client):
        """If GTIN exemption property is true use it instead of EAN."""
        AmazonExternalProductId.objects.filter(
            product=self.product,
            view=self.view,
        ).delete()

        AmazonGtinExemption.objects.create(
            product=self.product,
            view=self.view,
            value=True,
            multi_tenant_company=self.multi_tenant_company,
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

        self.assertEqual(
            attrs.get("supplier_declared_has_product_identifier_exemption"),
            [{"value": True, "marketplace_id": self.view.remote_id}],
        )
        self.assertNotIn("externally_assigned_product_identifier", attrs)

    @patch(
        "sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client",
        return_value=None,
    )
    @patch.object(
        AmazonMediaProductThroughBase,
        "_get_images",
        return_value=["https://example.com/img.jpg"],
    )
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_existing_remote_property_gets_updated(
        self, mock_listings, mock_get_images, mock_get_client
    ):
        """Simulate existing remote attribute and ensure update uses correct payload."""
        self.remote_product.created_marketplaces = [self.view.remote_id]
        self.remote_product.save()

        material_prop = baker.make(
            Property,
            type=Property.TYPES.TEXT,
            internal_name="material",
            multi_tenant_company=self.multi_tenant_company,
            is_public_information=True
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=material_prop,
            language=self.multi_tenant_company.language,
            name="Material",
        )
        pp = ProductProperty.objects.create(
            product=self.product,
            property=material_prop,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertyTextTranslation.objects.create(
            product_property=pp,
            language=self.multi_tenant_company.language,
            value_text="Wood",
            multi_tenant_company=self.multi_tenant_company,
        )

        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=material_prop,
            code="material",
            type=Property.TYPES.TEXT,
        )

        AmazonPublicDefinition.objects.create(
            api_region_code="EU_UK",
            product_type_code="CHAIR",
            code="material",
            name="Material",
            usage_definition=json.dumps(
                {
                    "material": [
                        {
                            "value": "%value:material%",
                            "marketplace_id": "%auto:marketplace_id%",
                        }
                    ]
                }
            ),
        )

        ProductPropertiesRuleItem.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=material_prop,
            defaults={"type": ProductPropertiesRuleItem.OPTIONAL},
        )

        mock_instance = mock_listings.return_value
        mock_instance.patch_listings_item.return_value = (
            self.get_put_and_patch_item_listing_mock_response()
        )
        current_attrs = {"material": [{"value": "Plastic", "marketplace_id": self.view.remote_id}]}
        mock_instance.get_listings_item.return_value = self.get_get_listing_item_mock_response(
            current_attrs
        )

        fac = AmazonProductSyncFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")
        patches = body.get("patches", [])

        material = self.get_patch_value(patches, "/attributes/material")

        self.assertEqual(
            material,
            [{"value": "Wood", "marketplace_id": self.view.remote_id}],
        )

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
        self.assertEqual(
            attrs.get("item_name"),
            [{
                "value": "Channel Name",
                "language_tag": "en",
                "marketplace_id": "GB",
            }],
        )
        self.assertEqual(
            attrs.get("product_description"),
            [{
                "value": "Channel Description",
                "language_tag": "en",
                "marketplace_id": "GB",
            }],
        )

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_translation_fallbacks_to_global_if_not_in_channel(self, mock_listings, mock_get_images, mock_get_client):
        """This test ensures fallback to global translation when channel-specific translation is missing."""
        ProductTranslation.objects.filter(product=self.product).delete()
        baker.make(
            ProductTranslation,
            product=self.product,
            sales_channel=None,
            language=self.multi_tenant_company.language,
            name="Global Name",
            description="Global Description",
            multi_tenant_company=self.multi_tenant_company,
        )

        baker.make(
            ProductTranslation,
            product=self.product,
            sales_channel=self.sales_channel,
            language=self.multi_tenant_company.language,
            name="Channel Name",
            description=None,
            multi_tenant_company=self.multi_tenant_company,
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

        self.assertEqual(
            attrs.get("item_name"),
            [{
                "value": "Channel Name",
                "language_tag": "en",
                "marketplace_id": "GB",
            }],
        )
        self.assertEqual(
            attrs.get("product_description"),
            [{
                "value": "Global Description",
                "language_tag": "en",
                "marketplace_id": "GB",
            }],
        )

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_price_sync_enabled_includes_price_fields(self, mock_listings, mock_get_images, mock_get_client):
        """Ensure price attributes are included when price sync is on."""
        self.sales_channel.sync_prices = True
        self.sales_channel.save()

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


        self.assertEqual(
            attrs.get("purchasable_offer"),
            [
                {
                    "audience": "ALL",
                    "currency": "GBP",
                    "marketplace_id": "GB",
                    "our_price": [
                        {"schedule": [{"value_with_tax": 80.0}]}
                    ],
                }
            ],
        )

        self.assertEqual(attrs.get("list_price"), [{"currency": "GBP", "marketplace_id": "GB", "value_with_tax": 80.0}])

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_price_sync_disabled_skips_price_fields(self, mock_listings, mock_get_images, mock_get_client):
        """This test ensures that price fields are skipped when price sync is turned off."""
        self.sales_channel.sync_prices = False
        self.sales_channel.save()

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

        self.assertNotIn("purchasable_offer", attrs)
        self.assertNotIn("list_price", attrs)

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_payload_skips_empty_price_fields_gracefully(self, mock_listings, mock_get_images, mock_get_client):
        """This test confirms that missing prices do not break payload generation and are omitted silently."""
        self.sales_channel.sync_prices = True
        self.sales_channel.save()

        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = {
            "submissionId": "mock-submission-id",
            "processingStatus": "VALID",
            "status": "VALID",
            "issues": [],
        }

        SalesPrice.objects.filter(product=self.product).delete()
        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()
        body = mock_listings.return_value.put_listings_item.call_args.kwargs.get("body")
        attrs = body.get("attributes", {})
        self.assertFalse(attrs.get("purchasable_offer"))
        self.assertFalse(attrs.get("list_price"))

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_price_update_when_values_differ_and_sync_enabled(self, mock_listings, mock_get_images, mock_get_client):
        """Ensure differing remote prices trigger an update when sync_prices is enabled."""
        self.sales_channel.sync_prices = True
        self.sales_channel.save()

        # product already exists remotely
        self.remote_product.created_marketplaces = [self.view.remote_id]
        self.remote_product.save()

        # adjust local price values
        price = SalesPrice.objects.get(product=self.product, currency=self.currency)
        price.price = 99.99
        price.save()

        mock_instance = mock_listings.return_value
        mock_instance.patch_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()
        mock_instance.get_listings_item.return_value = SimpleNamespace(
            attributes={
                "list_price": [{"currency": "GBP", "value_with_tax": 89.99}],
                "purchasable_offer": [
                    {
                        "audience": "ALL",
                        "currency": "GBP",
                        "marketplace_id": "GB",
                        "our_price": [
                            {"schedule": [{"value_with_tax": 89.99}]}
                        ],
                    }
                ],
            }
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

        purchasable_offer = self.get_patch_value(patches, "/attributes/purchasable_offer")
        list_price = self.get_patch_value(patches, "/attributes/list_price")

        self.assertEqual(
            purchasable_offer[0]["our_price"][0]["schedule"][0]["value_with_tax"],
            99.99,
        )
        self.assertEqual(
            list_price[0]["value_with_tax"],
            99.99,
        )

    def test_missing_view_argument_raises_value_error(self):
        """This test confirms that initializing a factory without a view raises ValueError."""
        factories = [
            AmazonProductCreateFactory,
            AmazonProductUpdateFactory,
            AmazonProductSyncFactory,
            AmazonProductDeleteFactory,
        ]

        for factory_class in factories:
            with self.assertRaises(ValueError):
                factory_class(
                    sales_channel=self.sales_channel,
                    local_instance=self.product,
                    remote_instance=self.remote_product,
                )

    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_update_product_fetches_attributes_when_missing(self, mock_listings):
        class Dummy(GetAmazonAPIMixin):
            def __init__(self, sales_channel, view):
                self.sales_channel = sales_channel
                self.view = view

            def _get_client(self):
                return None

            def get_identifiers(self):
                return 'test', 'test'

            def update_assign_issues(self, *args, **kwargs):
                pass

        dummy = Dummy(self.sales_channel, self.view)

        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

        with patch.object(
            dummy,
            "get_listing_attributes",
            return_value={
                "item_name": [
                    {
                        "value": "Old",
                        "language_tag": "en",
                        "marketplace_id": "GB",
                    }
                ]
            },
        ) as mock_get:
            product_type = AmazonProductType.objects.get(local_instance=self.rule)
            dummy.update_product(
                "AMZSKU",
                self.view.remote_id,
                product_type,
                {
                    "item_name": [
                        {
                            "value": "New",
                            "language_tag": "en",
                            "marketplace_id": "GB",
                        }
                    ]
                },
                None,
            )

            mock_get.assert_called_once_with("AMZSKU", self.view.remote_id)

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")
        patches = body["patches"]
        self.assertIn(
            {
                "op": "replace",
                "path": "/attributes/item_name",
                "value": [
                    {
                        "value": "New",
                        "language_tag": "en",
                        "marketplace_id": "GB",
                    }
                ],
            },
            patches,
        )


class AmazonProductCreateRequirementsTest(DisableWooCommerceSignalsMixin, TransactionTestCase, AmazonProductTestMixin):
    """Validate LISTING versus LISTING_OFFER_ONLY logic for product updates."""

    def setUp(self):
        super().setUp()
        self.setup_product()

    def _run_factory_and_get_body(self):
        with patch(
            "sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client",
            return_value=None,
        ), patch.object(
            AmazonMediaProductThroughBase,
            "_get_images",
            return_value=[],
        ), patch(
            "sales_channels.integrations.amazon.factories.mixins.ListingsApi"
        ) as mock_listings:
            mock_listings.return_value.put_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

            fac = AmazonProductCreateFactory(
                sales_channel=self.sales_channel,
                local_instance=self.product,
                remote_instance=self.remote_product,
                view=self.view,
            )
            fac.run()
            return mock_listings.return_value.put_listings_item.call_args.kwargs.get(
                "body"
            )

    def test_first_assign_with_asin_uses_listing_offer_only(self):
        body = self._run_factory_and_get_body()
        self.assertEqual(body["requirements"], "LISTING_OFFER_ONLY")

    def test_first_assign_without_asin_uses_listing(self):
        AmazonExternalProductId.objects.filter(
            product=self.product,
            view=self.view,
        ).update(type=AmazonExternalProductId.TYPE_GTIN, value="12345678901231")
        body = self._run_factory_and_get_body()
        self.assertEqual(body["requirements"], "LISTING")

    def test_not_first_assign_uses_listing_offer_only(self):
        self.remote_product.created_marketplaces = ["FR"]
        self.remote_product.save()
        body = self._run_factory_and_get_body()
        self.assertEqual(body["requirements"], "LISTING_OFFER_ONLY")


class AmazonConfigurablePropertySelectionTest(DisableWooCommerceSignalsMixin, TransactionTestCase, AmazonProductTestMixin):
    """Verify configurable product property detection with remote models."""

    def setUp(self):
        super().setUp()
        self.setup_product()

        self.product.type = Product.CONFIGURABLE
        self.product.save()
        self.parent = self.product

        self.rule, _ = ProductPropertiesRule.objects.get_or_create(
            product_type=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProductType.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.rule,
            product_type_code="CHAIR",
        )

        self.color_property, _ = Property.objects.get_or_create(
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
        self.color_red = baker.make(
            PropertySelectValue,
            property=self.color_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.color_blue = baker.make(
            PropertySelectValue,
            property=self.color_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.color_red,
            language=self.multi_tenant_company.language,
            value="Red",
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.color_blue,
            language=self.multi_tenant_company.language,
            value="Blue",
        )

        self.size_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            internal_name="size",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.size_property,
            language=self.multi_tenant_company.language,
            name="Size",
        )
        self.size_m = baker.make(
            PropertySelectValue,
            property=self.size_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.size_l = baker.make(
            PropertySelectValue,
            property=self.size_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.size_m,
            language=self.multi_tenant_company.language,
            value="M",
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.size_l,
            language=self.multi_tenant_company.language,
            value="L",
        )

        self.material_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            internal_name="material",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.material_property,
            language=self.multi_tenant_company.language,
            name="Material",
        )
        self.material_textile = baker.make(
            PropertySelectValue,
            property=self.material_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.material_plastic = baker.make(
            PropertySelectValue,
            property=self.material_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.material_textile,
            language=self.multi_tenant_company.language,
            value="Textile",
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.material_plastic,
            language=self.multi_tenant_company.language,
            value="Plastic",
        )

        self.items_property = baker.make(
            Property,
            type=Property.TYPES.INT,
            internal_name="number_of_items",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.items_property,
            language=self.multi_tenant_company.language,
            name="Number of items",
        )

        item_color, _ = ProductPropertiesRuleItem.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=self.color_property,
        )

        item_color.type = ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR
        item_color.save()

        ProductPropertiesRuleItem.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=self.size_property,
            type=ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR,
        )
        ProductPropertiesRuleItem.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=self.material_property,
            type=ProductPropertiesRuleItem.REQUIRED,
        )
        ProductPropertiesRuleItem.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=self.items_property,
            type=ProductPropertiesRuleItem.OPTIONAL,
        )

    def create_variation(self, sku, color, size, material, items):
        variation = baker.make(
            "products.Product",
            sku=sku,
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=variation,
            property=self.product_type_property,
            value_select=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=variation,
            property=self.color_property,
            value_select=color,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=variation,
            property=self.size_property,
            value_select=size,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=variation,
            property=self.material_property,
            value_select=material,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=variation,
            property=self.items_property,
            value_int=items,
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=self.parent,
            variation=variation,
        )
        return variation

    def _run_factory(self):
        fac = AmazonProductSyncFactory(
            sales_channel=self.sales_channel,
            local_instance=self.parent,
            view=self.view,
        )
        fac.set_rule()
        fac.set_product_properties()
        return sorted(pp.property.internal_name for pp in fac.product_properties)

    def test_scenario_one_shared_properties(self):
        """Scenario 1:
        - Red / M / Textile / 1
        - Blue / M / Textile / 2

        -> configurable properties: material, size
        """
        self.create_variation("V1", self.color_red, self.size_m, self.material_textile, 1)
        self.create_variation("V2", self.color_blue, self.size_m, self.material_textile, 2)
        names = self._run_factory()
        self.assertEqual(sorted(names), ["material", "size"])

    def test_scenario_two_shared_properties(self):
        """Scenario 2:
        - Red / M / Textile / 1
        - Blue / L /  Plastic / 1

        -> configurable properties: number_of_items
        """
        self.create_variation("V1", self.color_red, self.size_m, self.material_textile, 1)
        self.create_variation("V2", self.color_blue, self.size_l, self.material_plastic, 1)
        names = self._run_factory()
        self.assertEqual(sorted(names), ["number_of_items"])

    def test_scenario_three_shared_properties(self):
        """Scenario 3:
        - Red / M / Textile / 1
        - Red / L /  Textile / 1

        -> configurable properties: material, number_of_items
        """
        self.create_variation("V1", self.color_red, self.size_m, self.material_textile, 1)
        self.create_variation("V2", self.color_red, self.size_l, self.material_textile, 1)
        names = self._run_factory()
        self.assertEqual(sorted(names), ["material", "number_of_items"])


class AmazonConfigurableProductFlowTest(DisableWooCommerceSignalsMixin, TransactionTestCase, AmazonProductTestMixin):
    def setUp(self):
        super().setUp()
        self.setup_product()

        # make product configurable
        self.product.type = Product.CONFIGURABLE
        self.product.save()

        # add size property for variation theme matching
        self.size_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            internal_name="size",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.size_property,
            language=self.multi_tenant_company.language,
            name="Size",
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.size_property,
            code="size",
            type=Property.TYPES.SELECT,
        )
        ProductPropertiesRuleItem.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=self.size_property,
            defaults={"type": ProductPropertiesRuleItem.OPTIONAL},
        )

        # configure remote rule to allow theme
        self.remote_rule = AmazonProductType.objects.get(local_instance=self.rule)
        self.remote_rule.variation_themes = ["COLOR/SIZE", "SIZE"]
        self.remote_rule.save()

        # configurator with theme
        self.configurator = RemoteProductConfigurator.objects.create(
            remote_product=self.remote_product,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )
        self.configurator.properties.set([self.color_property, self.size_property])
        self.remote_product.save()
        AmazonVariationTheme.objects.create(
            product=self.product,
            view=self.view,
            theme="COLOR/SIZE",
            multi_tenant_company=self.multi_tenant_company,
        )

        # child product setup
        self.child = baker.make(
            "products.Product",
            sku="CHILD",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.child,
            property=self.product_type_property,
            value_select=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(multi_tenant_company=self.multi_tenant_company, parent=self.product, variation=self.child)
        AmazonExternalProductId.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.child,
            view=self.view,
            value="ASINCHILD",
        )

        self.child_remote = AmazonProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.child,
            remote_parent_product=self.remote_product,
            remote_sku="CHILD",
            is_variation=True,
        )

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_configurable_parent_payload_has_theme(self, mock_listings, mock_get_images, mock_get_client):
        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            view=self.view,
        )
        fac.run()

        calls = mock_instance.put_listings_item.call_args_list
        self.assertEqual(len(calls), 2)

        bodies = [call.kwargs.get("body", {}) for call in calls]

        # Organize parent & child based on 'parentage_level'
        parent_body = next(b for b in bodies if b["attributes"].get("parentage_level", [{}])[0]["value"] == "parent")
        child_body = next(b for b in bodies if b["attributes"].get("parentage_level", [{}])[0]["value"] == "child")

        # Shared expectations
        expected_theme = [{"name": "COLOR/SIZE", "marketplace_id": self.view.remote_id}]

        self.assertEqual(parent_body["attributes"].get("variation_theme"), expected_theme)
        self.assertEqual(parent_body["attributes"].get("parentage_level"),
                         [{"value": "parent", "marketplace_id": self.view.remote_id}])
        self.assertNotIn("child_parent_sku_relationship", parent_body["attributes"])
        self.assertEqual(
            parent_body["attributes"].get("color_name"),
            parent_body["attributes"].get("color"),
        )

        self.assertEqual(child_body["attributes"].get("variation_theme"), expected_theme)
        self.assertEqual(child_body["attributes"].get("parentage_level"),
                         [{"value": "child", "marketplace_id": self.view.remote_id}])
        self.assertEqual(
            child_body["attributes"].get("child_parent_sku_relationship"),
            [{
                "child_relationship_type": "variation",
                "marketplace_id": self.view.remote_id,
                "parent_sku": self.product.sku,  # or 'TESTSKU' if hardcoded
            }]
        )
        self.assertEqual(
            child_body["attributes"].get("color_name"),
            child_body["attributes"].get("color"),
        )

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_child_payload_has_variation_attributes(self, mock_listings, mock_get_images, mock_get_client):
        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.child,
            parent_local_instance=self.product,
            remote_parent_product=self.remote_product,
            remote_instance=self.child_remote,
            view=self.view,
        )
        fac.run()

        body = mock_instance.put_listings_item.call_args.kwargs.get("body")
        attrs = body.get("attributes", {})
        expected_theme = [{"name": "COLOR/SIZE", "marketplace_id": self.view.remote_id}]
        expected_parentage = [{"value": "child", "marketplace_id": self.view.remote_id}]
        expected_rel = [
            {
                "child_relationship_type": "variation",
                "parent_sku": "TESTSKU",
                "marketplace_id": self.view.remote_id,
            }
        ]

        self.assertEqual(attrs.get("variation_theme"), expected_theme)
        self.assertEqual(attrs.get("parentage_level"), expected_parentage)
        self.assertEqual(attrs.get("child_parent_sku_relationship"), expected_rel)
        self.assertEqual(attrs.get("color_name"), attrs.get("color"))

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch.object(AmazonMediaProductThroughBase, "_get_images", return_value=["https://example.com/img.jpg"])
    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_simple_product_has_no_variation_fields(self, mock_listings, mock_get_images, mock_get_client):
        simple = baker.make(
            "products.Product",
            sku="SIMPLE",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=simple,
            property=self.product_type_property,
            value_select=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonExternalProductId.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=simple,
            view=self.view,
            value="ASINSIMPLE",
        )
        simple_remote = AmazonProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=simple,
            remote_sku="SIMPLE",
        )

        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = self.get_put_and_patch_item_listing_mock_response()

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=simple,
            remote_instance=simple_remote,
            view=self.view,
        )
        fac.run()

        body = mock_instance.put_listings_item.call_args.kwargs.get("body")
        attrs = body.get("attributes", {})

        self.assertNotIn("variation_theme", attrs)
        self.assertNotIn("parentage_level", attrs)
        self.assertNotIn("child_parent_sku_relationship", attrs)


class AmazonProductFallbackValuesTest(DisableWooCommerceSignalsMixin, TestCase, AmazonProductTestMixin):
    def setUp(self):
        super().setUp()
        self.setup_product()
        self.default_view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="Default",
            api_region_code="EU_DE",
            remote_id="DE",
            is_default=True,
        )
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.default_view,
            remote_code="en",
        )
        AmazonExternalProductId.objects.filter(
            product=self.product,
            view=self.view,
        ).delete()
        AmazonGtinExemption.objects.filter(
            product=self.product,
            view=self.view,
        ).delete()
        AmazonVariationTheme.objects.filter(
            product=self.product,
            view=self.view,
        ).delete()
        AmazonExternalProductId.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            view=self.default_view,
            value="ASINDEF",
        )
        AmazonGtinExemption.objects.create(
            product=self.product,
            view=self.default_view,
            value=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        with patch(
            "sales_channels.integrations.amazon.models.products.AmazonVariationTheme.full_clean"
        ):
            AmazonVariationTheme.objects.create(
                product=self.product,
                view=self.default_view,
                theme="SIZE",
                multi_tenant_company=self.multi_tenant_company,
            )
        AmazonProductBrowseNode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel=self.sales_channel,
            view=self.default_view,
            recommended_browse_node_id="BN1",
        )

    def test_fallback_to_default_view(self):

        AmazonProductBrowseNode.objects.filter(
            view=self.view,
            product=self.product,
        ).delete()

        factory = AmazonProductBaseFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        ext = factory._get_external_product_id()
        self.assertIsNotNone(ext)
        self.assertEqual(ext.value, "ASINDEF")
        self.assertTrue(factory._get_gtin_exemption())
        self.assertEqual(factory._get_variation_theme(self.product), "SIZE")
        self.assertEqual(factory._get_recommended_browse_node_id(), "BN1")
        attrs = factory.build_basic_attributes()

        self.assertEqual(
            attrs.get("recommended_browse_nodes"),
            [{"value": "BN1", "marketplace_id": self.view.remote_id}],
        )
