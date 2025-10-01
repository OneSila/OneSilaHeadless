"""Tests for the EbayProductTypeRuleFactory."""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from typing import Any
from unittest.mock import patch

from properties.models import Property, ProductPropertiesRuleItem
from sales_channels.integrations.ebay.models import (
    EbayProductType,
    EbayProductTypeItem,
    EbayProperty,
    EbaySalesChannelView,
)
from sales_channels.integrations.ebay.models.properties import EbayPropertySelectValue

from .mixins import TestCaseEbayMixin


def _ensure_stubbed_ebay_rest() -> None:
    if "ebay_rest" in sys.modules:
        return

    ebay_rest = types.ModuleType("ebay_rest")

    class _StubAPI:  # pragma: no cover - simple stub to satisfy imports
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    ebay_rest.API = _StubAPI
    ebay_rest.token = types.ModuleType("ebay_rest.token")
    sys.modules["ebay_rest"] = ebay_rest

    reference_module = types.ModuleType("ebay_rest.reference")

    class _StubReference:
        @staticmethod
        def get_marketplace_id_values() -> dict[str, str]:
            return {}

    reference_module.Reference = _StubReference
    sys.modules["ebay_rest.reference"] = reference_module

    api_module = types.ModuleType("ebay_rest.api")
    sys.modules["ebay_rest.api"] = api_module

    commerce_identity_module = types.ModuleType("ebay_rest.api.commerce_identity")
    api_module.commerce_identity = commerce_identity_module
    sys.modules["ebay_rest.api.commerce_identity"] = commerce_identity_module

    commerce_identity_api_module = types.ModuleType("ebay_rest.api.commerce_identity.api")
    commerce_identity_module.api = commerce_identity_api_module
    sys.modules["ebay_rest.api.commerce_identity.api"] = commerce_identity_api_module

    user_api_module = types.ModuleType("ebay_rest.api.commerce_identity.api.user_api")

    class _StubUserApi:  # pragma: no cover - simple stub to satisfy imports
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    user_api_module.UserApi = _StubUserApi
    commerce_identity_api_module.user_api = user_api_module
    sys.modules["ebay_rest.api.commerce_identity.api.user_api"] = user_api_module

    sell_marketing_module = types.ModuleType("ebay_rest.api.sell_marketing")
    api_module.sell_marketing = sell_marketing_module
    sys.modules["ebay_rest.api.sell_marketing"] = sell_marketing_module

    api_client_module = types.ModuleType("ebay_rest.api.sell_marketing.api_client")

    class _StubApiClient:  # pragma: no cover - simple stub to satisfy imports
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    api_client_module.ApiClient = _StubApiClient
    sell_marketing_module.api_client = api_client_module
    sys.modules["ebay_rest.api.sell_marketing.api_client"] = api_client_module

    configuration_module = types.ModuleType("ebay_rest.api.sell_marketing.configuration")

    class _StubConfiguration:  # pragma: no cover - simple stub to satisfy imports
        def __init__(self) -> None:
            self.access_token: str | None = None
            self.host: str | None = None

    configuration_module.Configuration = _StubConfiguration
    sell_marketing_module.configuration = configuration_module
    sys.modules["ebay_rest.api.sell_marketing.configuration"] = configuration_module


@dataclass
class _DummyEbayAPI:
    category_response: dict[str, Any]
    aspects_response: dict[str, Any]

    def commerce_taxonomy_get_category_subtree(self, *, category_id: str, category_tree_id: str) -> dict[str, Any]:
        return self.category_response

    def commerce_taxonomy_get_item_aspects_for_category(self, *, category_id: str, category_tree_id: str) -> dict[str, Any]:
        return self.aspects_response


class TestEbayProductTypeRuleFactory(TestCaseEbayMixin):
    """Validate mapping logic for EbayProductTypeRuleFactory."""

    maxDiff = None

    def setUp(self) -> None:
        super().setUp()
        self.view = EbaySalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="EBAY_GB",
            default_category_tree_id="123",
            is_default=True,
        )

    def _build_category_response(self) -> dict[str, Any]:
        return {
            "category_subtree_node": {
                "category": {
                    "category_id": "3197",
                    "category_name": "Furniture",
                }
            }
        }

    def _build_aspects_response(self) -> dict[str, Any]:
        return {
            "aspects": [
                {
                    "localized_aspect_name": "Brand",
                    "aspect_constraint": {
                        "aspect_data_type": "STRING",
                        "item_to_aspect_cardinality": "SINGLE",
                        "aspect_mode": "FREE_TEXT",
                        "aspect_required": True,
                        "aspect_usage": "RECOMMENDED",
                        "aspect_enabled_for_variations": False,
                        "aspect_applicable_to": ["PRODUCT"],
                    },
                    "aspect_values": [
                        {"localized_value": "Unbranded"},
                        {"localized_value": "Apple"},
                    ],
                },
                {
                    "localized_aspect_name": "Color",
                    "aspect_constraint": {
                        "aspect_data_type": "STRING",
                        "item_to_aspect_cardinality": "SINGLE",
                        "aspect_mode": "FREE_TEXT",
                        "aspect_required": True,
                        "aspect_usage": "RECOMMENDED",
                        "aspect_enabled_for_variations": True,
                        "aspect_applicable_to": ["PRODUCT"],
                    },
                    "aspect_values": [
                        {"localized_value": "Black"},
                        {"localized_value": "Blue"},
                    ],
                },
                {
                    "localized_aspect_name": "Pattern",
                    "aspect_constraint": {
                        "aspect_data_type": "STRING",
                        "item_to_aspect_cardinality": "SINGLE",
                        "aspect_mode": "FREE_TEXT",
                        "aspect_required": False,
                        "aspect_usage": "OPTIONAL",
                        "aspect_enabled_for_variations": True,
                        "aspect_applicable_to": ["PRODUCT"],
                    },
                    "aspect_values": [
                        {"localized_value": "Striped"},
                        {"localized_value": "Solid"},
                    ],
                },
                {
                    "localized_aspect_name": "Connectivity",
                    "aspect_constraint": {
                        "aspect_data_type": "STRING",
                        "item_to_aspect_cardinality": "MULTI",
                        "aspect_mode": "FREE_TEXT",
                        "aspect_required": False,
                        "aspect_usage": "RECOMMENDED",
                        "aspect_enabled_for_variations": False,
                        "aspect_applicable_to": ["PRODUCT"],
                    },
                    "aspect_values": [
                        {"localized_value": "2G"},
                        {"localized_value": "3G"},
                        {"localized_value": "4G"},
                    ],
                },
                {
                    "localized_aspect_name": "EC Range",
                    "aspect_constraint": {
                        "aspect_data_type": "STRING",
                        "item_to_aspect_cardinality": "SINGLE",
                        "aspect_mode": "SELECTION_ONLY",
                        "aspect_required": False,
                        "aspect_usage": "RECOMMENDED",
                        "aspect_enabled_for_variations": False,
                        "aspect_applicable_to": ["PRODUCT"],
                    },
                    "aspect_values": [{"localized_value": "A - G"}],
                },
                {
                    "localized_aspect_name": "Energy Star",
                    "aspect_constraint": {
                        "aspect_data_type": "STRING",
                        "item_to_aspect_cardinality": "SINGLE",
                        "aspect_mode": "SELECTION_ONLY",
                        "aspect_required": False,
                        "aspect_usage": "RECOMMENDED",
                        "aspect_enabled_for_variations": False,
                        "aspect_applicable_to": ["PRODUCT"],
                    },
                    "aspect_values": [
                        {"localized_value": "A"},
                        {"localized_value": "B"},
                        {"localized_value": "C"},
                    ],
                },
                {
                    "localized_aspect_name": "Detailed Description",
                    "aspect_constraint": {
                        "aspect_data_type": "STRING",
                        "aspect_mode": "FREE_TEXT",
                        "aspect_required": False,
                        "aspect_usage": "OPTIONAL",
                        "aspect_enabled_for_variations": False,
                        "aspect_applicable_to": ["PRODUCT"],
                        "aspect_max_length": 1000,
                    },
                    "aspect_values": [],
                },
                {
                    "localized_aspect_name": "Material",
                    "aspect_constraint": {
                        "aspect_data_type": "STRING",
                        "aspect_mode": "FREE_TEXT",
                        "aspect_required": False,
                        "aspect_usage": "OPTIONAL",
                        "aspect_enabled_for_variations": False,
                        "aspect_applicable_to": ["PRODUCT"],
                        "aspect_max_length": 200,
                    },
                },
                {
                    "localized_aspect_name": "Voltage",
                    "aspect_constraint": {
                        "aspect_data_type": "STRING",
                        "aspect_mode": "FREE_TEXT",
                        "aspect_required": False,
                        "aspect_usage": "OPTIONAL",
                        "aspect_enabled_for_variations": False,
                        "aspect_applicable_to": ["PRODUCT"],
                        "aspect_advanced_data_type": "NUMERIC_RANGE",
                    },
                },
                {
                    "localized_aspect_name": "Screen Size",
                    "aspect_constraint": {
                        "aspect_data_type": "NUMBER",
                        "aspect_format": "double",
                        "aspect_mode": "FREE_TEXT",
                        "aspect_required": False,
                        "aspect_usage": "OPTIONAL",
                        "aspect_enabled_for_variations": False,
                        "aspect_applicable_to": ["PRODUCT"],
                    },
                },
                {
                    "localized_aspect_name": "Memory",
                    "aspect_constraint": {
                        "aspect_data_type": "NUMBER",
                        "aspect_format": "int32",
                        "aspect_mode": "FREE_TEXT",
                        "aspect_required": False,
                        "aspect_usage": "OPTIONAL",
                        "aspect_enabled_for_variations": False,
                        "aspect_applicable_to": ["PRODUCT"],
                    },
                },
                {
                    "localized_aspect_name": "Release Date",
                    "aspect_constraint": {
                        "aspect_data_type": "DATE",
                        "aspect_format": "YYYYMMDD",
                        "aspect_mode": "FREE_TEXT",
                        "aspect_required": False,
                        "aspect_usage": "OPTIONAL",
                        "aspect_enabled_for_variations": False,
                        "aspect_applicable_to": ["PRODUCT"],
                    },
                },
                {
                    "localized_aspect_name": "Warranty Expiration",
                    "aspect_constraint": {
                        "aspect_data_type": "DATE",
                        "aspect_format": "YYYYMMDDHHMMSS",
                        "aspect_mode": "FREE_TEXT",
                        "aspect_required": False,
                        "aspect_usage": "OPTIONAL",
                        "aspect_enabled_for_variations": False,
                        "aspect_applicable_to": ["PRODUCT"],
                    },
                },
                {
                    "localized_aspect_name": "Item Only",
                    "aspect_constraint": {
                        "aspect_data_type": "STRING",
                        "aspect_mode": "FREE_TEXT",
                        "aspect_applicable_to": ["ITEM"],
                    },
                },
            ]
        }

    def test_run_creates_remote_models_with_expected_mapping(self) -> None:
        _ensure_stubbed_ebay_rest()

        from sales_channels.integrations.ebay.factories.sales_channels.full_schema import (
            EbayProductTypeRuleFactory,
        )

        aspects_response = self._build_aspects_response()
        dummy_api = _DummyEbayAPI(
            category_response=self._build_category_response(),
            aspects_response=aspects_response,
        )

        category_aspects = {
            "Brand": {"Unbranded", "Apple"},
            "Connectivity": {"2G", "3G", "4G"},
        }

        with patch.object(EbayProductTypeRuleFactory, "get_api", return_value=dummy_api):
            factory = EbayProductTypeRuleFactory(
                sales_channel=self.sales_channel,
                view=self.view,
                category_id="3197",
                category_tree_id="123",
                category_aspects=category_aspects,
            )
            factory.run()

        product_type = EbayProductType.objects.get(
            sales_channel=self.sales_channel,
            remote_id="3197",
        )
        self.assertEqual(product_type.name, "Furniture")

        properties = {
            prop.localized_name: prop
            for prop in EbayProperty.objects.filter(
                sales_channel=self.sales_channel,
                marketplace=self.view,
            )
        }

        self.assertNotIn("Item Only", properties)
        expected_property_names = {
            "Brand",
            "Color",
            "Pattern",
            "Connectivity",
            "EC Range",
            "Energy Star",
            "Detailed Description",
            "Material",
            "Voltage",
            "Screen Size",
            "Memory",
            "Release Date",
            "Warranty Expiration",
        }
        self.assertEqual(set(properties), expected_property_names)

        self.assertEqual(properties["Brand"].type, Property.TYPES.SELECT)
        self.assertTrue(properties["Brand"].allows_unmapped_values)
        self.assertEqual(properties["Color"].type, Property.TYPES.SELECT)
        self.assertEqual(properties["Connectivity"].type, Property.TYPES.MULTISELECT)
        self.assertEqual(properties["EC Range"].type, Property.TYPES.SELECT)
        self.assertFalse(properties["EC Range"].allows_unmapped_values)
        self.assertEqual(properties["Detailed Description"].type, Property.TYPES.DESCRIPTION)
        self.assertEqual(properties["Material"].type, Property.TYPES.TEXT)
        self.assertEqual(properties["Voltage"].type, Property.TYPES.TEXT)
        self.assertEqual(properties["Screen Size"].type, Property.TYPES.FLOAT)
        self.assertEqual(properties["Memory"].type, Property.TYPES.INT)
        self.assertEqual(properties["Release Date"].type, Property.TYPES.DATE)
        self.assertEqual(properties["Warranty Expiration"].type, Property.TYPES.DATETIME)
        self.assertEqual(properties["Release Date"].value_format, "YYYYMMDD")
        self.assertEqual(properties["Warranty Expiration"].value_format, "YYYYMMDDHHMMSS")

        brand_values = {
            value.localized_value
            for value in EbayPropertySelectValue.objects.filter(ebay_property=properties["Brand"])
        }
        self.assertEqual(brand_values, {"Unbranded", "Apple"})

        connectivity_values = {
            value.localized_value
            for value in EbayPropertySelectValue.objects.filter(ebay_property=properties["Connectivity"])
        }
        self.assertEqual(connectivity_values, {"2G", "3G", "4G"})

        items = {
            item.ebay_property.localized_name: item.remote_type
            for item in EbayProductTypeItem.objects.filter(product_type=product_type)
        }

        self.assertEqual(items["Brand"], ProductPropertiesRuleItem.REQUIRED)
        self.assertEqual(items["Color"], ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR)
        self.assertEqual(items["Pattern"], ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR)
        self.assertEqual(items["Connectivity"], ProductPropertiesRuleItem.OPTIONAL)
        self.assertEqual(items["EC Range"], ProductPropertiesRuleItem.OPTIONAL)
        self.assertEqual(items["Detailed Description"], ProductPropertiesRuleItem.OPTIONAL)
