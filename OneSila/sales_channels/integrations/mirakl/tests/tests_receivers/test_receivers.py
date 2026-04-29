from unittest.mock import patch

from model_bakery import baker

from core.tests import TestCase
from products.models import ConfigurableVariation, Product
from properties.models import (
    ProductPropertiesRule,
    ProductPropertiesRuleItem,
    Property,
    PropertySelectValue,
)
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklProductCategory,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklSalesChannel,
)
from sales_channels.integrations.shopify.models import ShopifySalesChannel
from sales_channels.signals import refresh_website_pull_models
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklMetadataReceiverTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )

    @patch("sales_channels.integrations.mirakl.factories.sales_channels.MiraklRemoteCurrencyPullFactory")
    @patch("sales_channels.integrations.mirakl.factories.sales_channels.MiraklRemoteLanguagePullFactory")
    @patch("sales_channels.integrations.mirakl.factories.sales_channels.MiraklSalesChannelViewPullFactory")
    def test_refresh_signal_runs_three_metadata_factories(
        self,
        view_factory_cls,
        language_factory_cls,
        currency_factory_cls,
    ):
        refresh_website_pull_models.send(
            sender=self.sales_channel.__class__,
            instance=self.sales_channel,
        )

        view_factory_cls.assert_called_once_with(sales_channel=self.sales_channel)
        language_factory_cls.assert_called_once_with(sales_channel=self.sales_channel)
        currency_factory_cls.assert_called_once_with(sales_channel=self.sales_channel)
        view_factory_cls.return_value.run.assert_called_once_with()
        language_factory_cls.return_value.run.assert_called_once_with()
        currency_factory_cls.return_value.run.assert_called_once_with()

    @patch("sales_channels.integrations.mirakl.factories.sales_channels.MiraklRemoteCurrencyPullFactory")
    @patch("sales_channels.integrations.mirakl.factories.sales_channels.MiraklRemoteLanguagePullFactory")
    @patch("sales_channels.integrations.mirakl.factories.sales_channels.MiraklSalesChannelViewPullFactory")
    def test_non_mirakl_channel_is_ignored(
        self,
        view_factory_cls,
        language_factory_cls,
        currency_factory_cls,
    ):
        shopify_channel = baker.make(
            ShopifySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://shop.example.com",
        )

        refresh_website_pull_models.send(
            sender=shopify_channel.__class__,
            instance=shopify_channel,
        )

        view_factory_cls.assert_not_called()
        language_factory_cls.assert_not_called()
        currency_factory_cls.assert_not_called()


class MiraklPropertySelectValueReceiverTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )
        self.local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        self.local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=self.local_property,
        )
        self.remote_property = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="color",
            type=Property.TYPES.SELECT,
            local_instance=self.local_property,
        )

    @patch("sales_channels.integrations.mirakl.factories.sync.MiraklPropertySelectValueSiblingMappingFactory")
    def test_post_create_runs_propagation_for_mapped_select_value(self, sync_factory_cls):
        remote_value = baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=self.remote_property,
            code="purple",
            value="Purple",
            local_instance=self.local_value,
        )

        sync_factory_cls.assert_called_once_with(remote_select_value=remote_value)
        sync_factory_cls.return_value.run.assert_called_once_with()

    @patch("sales_channels.integrations.mirakl.factories.sync.MiraklPropertySelectValueSiblingMappingFactory")
    def test_post_update_runs_propagation_only_when_local_mapping_changes(self, sync_factory_cls):
        remote_value = baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=self.remote_property,
            code="purple",
            value="Purple",
            local_instance=None,
        )
        sync_factory_cls.reset_mock()

        remote_value.local_instance = self.local_value
        remote_value.save(update_fields=["local_instance"])

        sync_factory_cls.assert_called_once_with(remote_select_value=remote_value)
        sync_factory_cls.return_value.run.assert_called_once_with()

    @patch("sales_channels.integrations.mirakl.factories.sync.MiraklPropertySelectValueSiblingMappingFactory")
    def test_post_update_ignores_non_mapping_updates(self, sync_factory_cls):
        remote_value = baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=self.remote_property,
            code="purple",
            value="Purple",
            local_instance=None,
        )
        sync_factory_cls.reset_mock()

        remote_value.value = "Purple Updated"
        remote_value.save(update_fields=["value"])

        sync_factory_cls.assert_not_called()


class MiraklProductTypeReceiverTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )
        self.category = baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CAT-1",
            name="Category",
            is_leaf=True,
        )
        self.local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        self.remote_property = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="material",
            type=Property.TYPES.TEXT,
            local_instance=self.local_property,
        )
        self.source_product_type = baker.make(
            MiraklProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            category=self.category,
            remote_id="CAT-1",
            local_instance=None,
            name="Category",
            imported=True,
        )
        self.source_item = baker.make(
            MiraklProductTypeItem,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type=self.source_product_type,
            remote_property=self.remote_property,
            hierarchy_code="CAT-1",
            required=True,
            variant=True,
            requirement_level="REQUIRED",
            value_list_code="MATERIAL_LIST",
            value_list_label="Materials",
            raw_data={"code": "material"},
        )

    def _create_local_rule(self):
        product_type_property = Property.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True,
        )
        product_type_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=product_type_property,
        )
        rule = baker.make(
            ProductPropertiesRule,
            multi_tenant_company=self.multi_tenant_company,
            product_type=product_type_value,
            sales_channel=self.sales_channel,
        )
        rule_item = baker.make(
            ProductPropertiesRuleItem,
            multi_tenant_company=self.multi_tenant_company,
            rule=rule,
            property=self.local_property,
            type=ProductPropertiesRuleItem.REQUIRED,
        )
        return rule, rule_item

    def test_post_create_does_not_clone_items(self):
        rule, _ = self._create_local_rule()

        target_product_type = baker.make(
            MiraklProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CAT-1",
            local_instance=rule,
            imported=False,
        )

        self.assertFalse(
            MiraklProductTypeItem.objects.filter(
                product_type=target_product_type,
            ).exists()
        )

    def test_post_update_clones_items_when_remote_id_is_mapped_later(self):
        rule, rule_item = self._create_local_rule()
        target_product_type = baker.make(
            MiraklProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="",
            local_instance=rule,
            imported=False,
        )

        target_product_type.remote_id = "CAT-1"
        target_product_type.save(update_fields=["remote_id"])

        cloned_item = MiraklProductTypeItem.objects.get(
            product_type=target_product_type,
            remote_property=self.remote_property,
        )
        self.assertEqual(cloned_item.local_instance, rule_item)
        self.assertEqual(cloned_item.hierarchy_code, self.source_item.hierarchy_code)
        self.assertEqual(cloned_item.value_list_code, self.source_item.value_list_code)
        self.assertTrue(cloned_item.required)
        target_product_type.refresh_from_db()
        self.assertEqual(target_product_type.category, self.category)
        self.assertEqual(target_product_type.name, "Category")

    def test_post_update_does_not_clone_when_target_already_has_items(self):
        rule, _ = self._create_local_rule()
        target_product_type = baker.make(
            MiraklProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="",
            local_instance=rule,
            imported=False,
        )
        existing_property = baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="existing",
            type=Property.TYPES.TEXT,
        )
        existing_item = baker.make(
            MiraklProductTypeItem,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type=target_product_type,
            remote_property=existing_property,
        )

        target_product_type.remote_id = "CAT-1"
        target_product_type.save(update_fields=["remote_id"])

        self.assertEqual(
            list(
                MiraklProductTypeItem.objects.filter(
                    product_type=target_product_type,
                )
            ),
            [existing_item],
        )
        self.assertFalse(
            MiraklProductTypeItem.objects.filter(
                product_type=target_product_type,
                remote_property=self.remote_property,
            ).exists()
        )


class MiraklProductCategoryReceiverTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )
        self.category = baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="leaf-1",
            name="Leaf",
            is_leaf=True,
        )
        self.parent_product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            sku="PARENT-1",
        )
        self.child_product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="CHILD-1",
        )
        baker.make(
            ConfigurableVariation,
            multi_tenant_company=self.multi_tenant_company,
            parent=self.parent_product,
            variation=self.child_product,
        )

    def test_post_create_propagates_parent_category_to_variations(self):
        MiraklProductCategory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.parent_product,
            remote_id="leaf-1",
        )

        self.assertTrue(
            MiraklProductCategory.objects.filter(
                product=self.child_product,
                sales_channel=self.sales_channel,
                remote_id="leaf-1",
            ).exists()
        )

    def test_post_update_updates_variation_category(self):
        other_category = baker.make(
            MiraklCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="leaf-2",
            name="Leaf 2",
            is_leaf=True,
        )
        parent_mapping = MiraklProductCategory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.parent_product,
            remote_id="leaf-1",
        )
        child_mapping = MiraklProductCategory.objects.get(
            product=self.child_product,
            sales_channel=self.sales_channel,
        )
        self.assertEqual(child_mapping.remote_id, "leaf-1")

        parent_mapping.remote_id = other_category.remote_id
        parent_mapping.save(update_fields=["remote_id"])

        child_mapping.refresh_from_db()
        self.assertEqual(child_mapping.remote_id, "leaf-2")
