"""Tests for the Shein category tree synchronisation factory."""

from __future__ import annotations

from unittest.mock import Mock, patch

from core.tests import TestCase
from model_bakery import baker
from properties.models import Property

from sales_channels.integrations.shein.factories.sales_channels.full_schema import (
    SheinCategoryTreeSyncFactory,
)
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinProductType,
    SheinProductTypeItem,
    SheinProperty,
    SheinPropertySelectValue,
    SheinRemoteLanguage,
    SheinSalesChannel,
    SheinSalesChannelView,
)
from sales_channels.integrations.shein.models.imports import SheinSalesChannelImport


CATEGORY_TREE_PAYLOAD = {
    "code": "0",
    "msg": "OK",
    "info": {
        "data": [
            {
                "category_id": 2028,
                "parent_category_id": 0,
                "category_name": "女士",
                "last_category": False,
                "children": [
                    {
                        "category_id": 2033,
                        "parent_category_id": 2028,
                        "category_name": "Clothing",
                        "last_category": False,
                        "children": [
                            {
                                "category_id": 1767,
                                "parent_category_id": 2033,
                                "category_name": "Dresses中文",
                                "last_category": False,
                                "children": [
                                    {
                                        "category_id": 1727,
                                        "product_type_id": 1080,
                                        "parent_category_id": 1767,
                                        "category_name": "Dresses/中文-四级",
                                        "last_category": True,
                                        "children": [],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    },
}

PUBLISH_STANDARD_INFO = {
    "default_language": "en",
    "currency": "GBP",
    "support_sale_attribute_sort": False,
    "fill_configuration_tags": ["PACKAGE_TYPE_TO_SKU"],
    "picture_config_list": [
        {"field_key": "spu_image_detail_show", "is_true": True},
        {"field_key": "skc_image_square_required", "is_true": False},
    ],
    "fill_in_standard_list": [
        {
            "module": "reference_info",
            "field_key": "reference_product_link",
            "required": True,
            "show": True,
        },
        {
            "module": "reference_info",
            "field_key": "proof_of_stock",
            "required": False,
            "show": False,
        },
        {
            "module": "sales_info",
            "field_key": "shelf_require",
            "required": True,
            "show": True,
        },
        {
            "module": "basic_info",
            "field_key": "brand_code",
            "required": True,
            "show": True,
        },
        {
            "module": "basic_info",
            "field_key": "skc_title",
            "required": False,
            "show": True,
        },
        {
            "module": "supplier_info",
            "field_key": "minimum_stock_quantity",
            "required": True,
            "show": True,
        },
        {
            "module": "basic_info",
            "field_key": "product_detail_picture",
            "required": True,
            "show": True,
        },
        {
            "module": "basic_info",
            "field_key": "quantity_info",
            "required": False,
            "show": True,
        },
        {
            "module": "basic_info",
            "field_key": "sample_spec",
            "required": False,
            "show": True,
        },
        {
            "module": "supplier_info",
            "field_key": "package_type",
            "required": False,
            "show": True,
        },
        {
            "module": "supplier_info",
            "field_key": "supplier_barcode",
            "required": True,
            "show": True,
        },
    ],
}

ATTRIBUTE_TEMPLATE_RESPONSE = {
    "code": "0",
    "msg": "OK",
    "info": {
        "data": [
            {
                "product_type_id": 1080,
                "attribute_infos": [
                    {
                        "attribute_id": 27,
                        "attribute_name": "颜色",
                        "attribute_name_en": "Color",
                        "attribute_is_show": 1,
                        "attribute_source": 1,
                        "attribute_label": 1,
                        "attribute_mode": 1,
                        "attribute_input_num": 0,
                        "data_dimension": 1,
                        "attribute_status": 3,
                        "attribute_type": 1,
                        "business_mode": 1,
                        "is_sample": 0,
                        "supplier_id": 0,
                        "attribute_doc": "Select a color",
                        "attribute_doc_image_list": [],
                        "attribute_remark_list": [1, 3],
                        "attribute_value_info_list": [
                            {
                                "attribute_value_id": 78,
                                "attribute_value": "杏色",
                                "attribute_value_en": "Apricot",
                                "is_custom_attribute_value": False,
                                "is_show": 1,
                                "supplier_id": 0,
                                "attribute_value_doc": None,
                                "attribute_value_doc_image_list": None,
                                "attribute_value_group_list": None,
                            },
                            {
                                "attribute_value_id": 103,
                                "attribute_value": "米色",
                                "attribute_value_en": "Beige",
                                "is_custom_attribute_value": False,
                                "is_show": 1,
                                "supplier_id": 0,
                                "attribute_value_doc": None,
                                "attribute_value_doc_image_list": None,
                                "attribute_value_group_list": None,
                            },
                        ],
                    },
                    {
                        "attribute_id": 87,
                        "attribute_name": "尺寸",
                        "attribute_name_en": "Size",
                        "attribute_is_show": 2,
                        "attribute_source": 1,
                        "attribute_label": 0,
                        "attribute_mode": 2,
                        "data_dimension": 1,
                        "attribute_status": 2,
                        "attribute_type": 2,
                        "business_mode": 1,
                        "is_sample": 1,
                        "supplier_id": 0,
                        "attribute_doc": None,
                        "attribute_doc_image_list": None,
                        "attribute_value_info_list": [
                            {
                                "attribute_value_id": 474,
                                "attribute_value": "单一尺寸",
                                "attribute_value_en": "One size",
                                "is_custom_attribute_value": False,
                                "is_show": 1,
                                "supplier_id": 0,
                                "attribute_value_doc": None,
                                "attribute_value_doc_image_list": None,
                                "attribute_value_group_list": None,
                            }
                        ],
                    },
                ],
            }
        ]
    },
}

CUSTOM_ATTRIBUTE_PERMISSION_RESPONSE = {
    "code": "0",
    "msg": "OK",
    "info": {
        "data": [
            {
                "has_permission": 1,
                "last_category_id": 1727,
                "attribute_id": 27,
            },
            {
                "has_permission": 1,
                "last_category_id": 1727,
                "attribute_id": 87,
            },
        ],
    },
}


class SheinCategoryTreeFactoryTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            hostname="https://fr.shein.com",
            multi_tenant_company=self.multi_tenant_company,
            open_key_id="open-key",
            secret_key="secret-key",
        )
        self.view = baker.make(
            SheinSalesChannelView,
            sales_channel=self.sales_channel,
            remote_id="shein-fr",
            is_default=True,
        )

    def test_run_creates_categories_and_product_types(self) -> None:
        factory = SheinCategoryTreeSyncFactory(sales_channel=self.sales_channel, view=self.view)

        def fake_post(*, path: str, payload=None, **kwargs):  # type: ignore[no-untyped-def]
            if path == factory.category_tree_path:
                self.assertEqual(payload, {"site_abbr": self.view.remote_id})
                tree_response = Mock()
                tree_response.json.return_value = CATEGORY_TREE_PAYLOAD
                return tree_response

            if path == factory.publish_standard_path:
                self.assertIn("category_id", payload)
                publish_response = Mock()
                publish_response.json.return_value = {"info": PUBLISH_STANDARD_INFO}
                return publish_response

            if path == factory.attribute_template_path:
                self.assertEqual(payload, {"product_type_id_list": [1080]})
                attribute_response = Mock()
                attribute_response.json.return_value = ATTRIBUTE_TEMPLATE_RESPONSE
                return attribute_response

            if path == factory.custom_attribute_permission_path:
                self.assertEqual(payload, {"category_id_list": [1727]})
                permission_response = Mock()
                permission_response.json.return_value = CUSTOM_ATTRIBUTE_PERMISSION_RESPONSE
                return permission_response

            self.fail(f"Unexpected Shein API path invoked: {path}")

        with patch.object(SheinCategoryTreeSyncFactory, "shein_post", side_effect=fake_post) as mock_post:
            categories = factory.run()

        # Tree call + publish calls per category + attribute template + custom permissions
        self.assertEqual(mock_post.call_count, SheinCategory.objects.count() + 3)

        self.assertEqual(len(categories), SheinCategory.objects.count())
        self.assertEqual(SheinCategory.objects.count(), 4)
        self.assertEqual(
            SheinCategory.objects.filter(site_remote_id=self.view.remote_id).count(),
            4,
        )
        self.assertEqual(SheinProductType.objects.count(), 1)
        self.assertEqual(SheinProperty.objects.count(), 2)
        self.assertEqual(SheinPropertySelectValue.objects.count(), 3)
        self.assertEqual(SheinProductTypeItem.objects.count(), 2)

        root_category = SheinCategory.objects.get(remote_id="2028")
        self.assertIsNone(root_category.parent)
        self.assertFalse(root_category.is_leaf)
        self.assertEqual(root_category.site_remote_id, self.view.remote_id)
        self.assertNotIn("children", root_category.raw_data)
        self.assertEqual(root_category.default_language, PUBLISH_STANDARD_INFO["default_language"])
        self.assertEqual(root_category.currency, PUBLISH_STANDARD_INFO["currency"])
        self.assertTrue(root_category.reference_info_required)
        self.assertTrue(root_category.reference_product_link_required)
        self.assertFalse(root_category.proof_of_stock_required)
        self.assertTrue(root_category.shelf_require_required)
        self.assertTrue(root_category.brand_code_required)
        self.assertFalse(root_category.skc_title_required)
        self.assertTrue(root_category.minimum_stock_quantity_required)
        self.assertTrue(root_category.product_detail_picture_required)
        self.assertFalse(root_category.quantity_info_required)
        self.assertFalse(root_category.sample_spec_required)
        self.assertEqual(root_category.picture_config, PUBLISH_STANDARD_INFO["picture_config_list"])
        self.assertFalse(root_category.support_sale_attribute_sort)
        self.assertTrue(root_category.package_type_required)
        self.assertTrue(root_category.supplier_barcode_required)
        self.assertEqual(root_category.configurator_properties, [])

        leaf_category = SheinCategory.objects.get(remote_id="1727")
        self.assertTrue(leaf_category.is_leaf)
        self.assertEqual(leaf_category.parent_remote_id, "1767")
        self.assertEqual(leaf_category.site_remote_id, self.view.remote_id)
        self.assertEqual(leaf_category.product_type_remote_id, "1080")
        self.assertEqual(leaf_category.default_language, PUBLISH_STANDARD_INFO["default_language"])
        self.assertEqual(leaf_category.currency, PUBLISH_STANDARD_INFO["currency"])
        self.assertTrue(leaf_category.reference_info_required)
        self.assertTrue(leaf_category.reference_product_link_required)
        self.assertFalse(leaf_category.proof_of_stock_required)
        self.assertTrue(leaf_category.shelf_require_required)
        self.assertTrue(leaf_category.brand_code_required)
        self.assertFalse(leaf_category.skc_title_required)
        self.assertTrue(leaf_category.minimum_stock_quantity_required)
        self.assertTrue(leaf_category.product_detail_picture_required)
        self.assertFalse(leaf_category.quantity_info_required)
        self.assertFalse(leaf_category.sample_spec_required)
        self.assertEqual(leaf_category.picture_config, PUBLISH_STANDARD_INFO["picture_config_list"])
        self.assertFalse(leaf_category.support_sale_attribute_sort)
        self.assertTrue(leaf_category.package_type_required)
        self.assertTrue(leaf_category.supplier_barcode_required)
        self.assertEqual({entry.get("property_id") for entry in leaf_category.configurator_properties}, {"27", "87"})

        product_type = SheinProductType.objects.get(remote_id="1080")
        self.assertEqual(product_type.category_id, leaf_category.remote_id)
        self.assertEqual(product_type.name, leaf_category.name)
        self.assertNotIn("children", product_type.raw_data)
        self.assertIn(product_type, factory.synced_product_types)

        color_property = SheinProperty.objects.get(remote_id="27")
        self.assertEqual(color_property.value_mode, SheinProperty.ValueModes.MULTI_SELECT)
        self.assertEqual(color_property.type, Property.TYPES.MULTISELECT)
        self.assertEqual(color_property.attribute_doc, "Select a color")

        size_property = SheinProperty.objects.get(remote_id="87")
        self.assertEqual(size_property.value_mode, SheinProperty.ValueModes.SALES_SINGLE_SELECT)
        self.assertEqual(size_property.type, Property.TYPES.SELECT)
        self.assertTrue(size_property.is_sample)

        color_values = SheinPropertySelectValue.objects.filter(remote_property=color_property)
        self.assertEqual(color_values.count(), 2)
        self.assertTrue(color_values.filter(value_en="Apricot").exists())

        product_type_items = SheinProductTypeItem.objects.filter(product_type=product_type)
        self.assertEqual(product_type_items.count(), 2)
        color_item = product_type_items.get(property=color_property)
        self.assertEqual(color_item.visibility, SheinProductTypeItem.Visibility.DISPLAY)
        self.assertEqual(color_item.attribute_type, SheinProductTypeItem.AttributeType.SALES)
        self.assertEqual(color_item.requirement, SheinProductTypeItem.Requirement.REQUIRED)
        self.assertTrue(color_item.is_main_attribute)
        self.assertIn(SheinProductTypeItem.RemarkTags.IMPORTANT, color_item.remarks)
        self.assertTrue(color_item.allows_unmapped_values)

        size_item = product_type_items.get(property=size_property)
        self.assertEqual(size_item.visibility, SheinProductTypeItem.Visibility.HIDDEN)
        self.assertEqual(size_item.attribute_type, SheinProductTypeItem.AttributeType.SIZE)
        self.assertEqual(size_item.requirement, SheinProductTypeItem.Requirement.OPTIONAL)
        self.assertFalse(size_item.is_main_attribute)
        self.assertTrue(size_item.allows_unmapped_values)

        remote_languages = self.view.remote_languages.all()
        self.assertEqual(remote_languages.count(), 1)
        remote_language = remote_languages.first()
        self.assertIsNotNone(remote_language)
        self.assertEqual(remote_language.remote_code, PUBLISH_STANDARD_INFO["default_language"])
        self.assertEqual(remote_language.local_instance, PUBLISH_STANDARD_INFO["default_language"])
        self.assertEqual(remote_language.remote_name, "English")
        self.assertEqual(SheinRemoteLanguage.objects.count(), 1)

    def test_run_updates_import_process_percentage_when_provided(self) -> None:
        import_process = baker.make(
            SheinSalesChannelImport,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            percentage=0,
        )
        factory = SheinCategoryTreeSyncFactory(
            sales_channel=self.sales_channel,
            view=self.view,
            import_process=import_process,
        )
        nodes = CATEGORY_TREE_PAYLOAD["info"]["data"]
        factory._sync_category = Mock(return_value=object())  # type: ignore[attr-defined]

        factory.run(tree=nodes)

        import_process.refresh_from_db()
        self.assertEqual(import_process.percentage, 100)

    def test_run_uses_provided_tree_without_remote_call(self) -> None:
        tree = CATEGORY_TREE_PAYLOAD["info"]["data"]
        factory = SheinCategoryTreeSyncFactory(sales_channel=self.sales_channel, view=self.view)

        with patch.object(
            SheinCategoryTreeSyncFactory,
            "_fetch_publish_fill_in_standard",
            return_value=PUBLISH_STANDARD_INFO,
        ) as mock_fill, patch.object(
            SheinCategoryTreeSyncFactory,
            "_fetch_attribute_template",
            return_value=ATTRIBUTE_TEMPLATE_RESPONSE["info"]["data"][0]["attribute_infos"],
        ) as mock_attr, patch.object(
            SheinCategoryTreeSyncFactory,
            "_fetch_custom_attribute_permissions",
            return_value={"27": True, "87": True},
        ) as mock_perm, patch.object(SheinCategoryTreeSyncFactory, "shein_post") as mock_post:
            categories = factory.run(tree=tree)

        mock_post.assert_not_called()
        self.assertEqual(mock_fill.call_count, 4)
        self.assertEqual(mock_attr.call_count, 1)
        self.assertEqual(mock_perm.call_count, 1)
        self.assertEqual(SheinCategory.objects.count(), 4)
        self.assertEqual(len(categories), 4)
        self.assertEqual(SheinProductType.objects.count(), 1)
        self.assertEqual(SheinProductTypeItem.objects.count(), 2)
