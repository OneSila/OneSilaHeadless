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
            "categorySubtreeNode": {
                "category": {
                    "categoryId": "3197",
                    "categoryName": "Furniture",
                }
            }
        }

    def _build_aspects_response(self) -> dict[str, Any]:
        return {
            "aspects": [
                {
                    "localizedAspectName": "Brand",
                    "aspectConstraint": {
                        "aspectDataType": "STRING",
                        "itemToAspectCardinality": "SINGLE",
                        "aspectMode": "FREE_TEXT",
                        "aspectRequired": True,
                        "aspectUsage": "RECOMMENDED",
                        "aspectEnabledForVariations": False,
                        "aspectApplicableTo": ["PRODUCT"],
                    },
                    "aspectValues": [
                        {"localizedValue": "Unbranded"},
                        {"localizedValue": "Apple"},
                    ],
                },
                {
                    "localizedAspectName": "Color",
                    "aspectConstraint": {
                        "aspectDataType": "STRING",
                        "itemToAspectCardinality": "SINGLE",
                        "aspectMode": "FREE_TEXT",
                        "aspectRequired": True,
                        "aspectUsage": "RECOMMENDED",
                        "aspectEnabledForVariations": True,
                        "aspectApplicableTo": ["PRODUCT"],
                    },
                    "aspectValues": [
                        {"localizedValue": "Black"},
                        {"localizedValue": "Blue"},
                    ],
                },
                {
                    "localizedAspectName": "Pattern",
                    "aspectConstraint": {
                        "aspectDataType": "STRING",
                        "itemToAspectCardinality": "SINGLE",
                        "aspectMode": "FREE_TEXT",
                        "aspectRequired": False,
                        "aspectUsage": "OPTIONAL",
                        "aspectEnabledForVariations": True,
                        "aspectApplicableTo": ["PRODUCT"],
                    },
                    "aspectValues": [
                        {"localizedValue": "Striped"},
                        {"localizedValue": "Solid"},
                    ],
                },
                {
                    "localizedAspectName": "Connectivity",
                    "aspectConstraint": {
                        "aspectDataType": "STRING",
                        "itemToAspectCardinality": "MULTI",
                        "aspectMode": "FREE_TEXT",
                        "aspectRequired": False,
                        "aspectUsage": "RECOMMENDED",
                        "aspectEnabledForVariations": False,
                        "aspectApplicableTo": ["PRODUCT"],
                    },
                    "aspectValues": [
                        {"localizedValue": "2G"},
                        {"localizedValue": "3G"},
                        {"localizedValue": "4G"},
                    ],
                },
                {
                    "localizedAspectName": "EC Range",
                    "aspectConstraint": {
                        "aspectDataType": "STRING",
                        "itemToAspectCardinality": "SINGLE",
                        "aspectMode": "SELECTION_ONLY",
                        "aspectRequired": False,
                        "aspectUsage": "RECOMMENDED",
                        "aspectEnabledForVariations": False,
                        "aspectApplicableTo": ["PRODUCT"],
                    },
                    "aspectValues": [{"localizedValue": "A - G"}],
                },
                {
                    "localizedAspectName": "Energy Star",
                    "aspectConstraint": {
                        "aspectDataType": "STRING",
                        "itemToAspectCardinality": "SINGLE",
                        "aspectMode": "SELECTION_ONLY",
                        "aspectRequired": False,
                        "aspectUsage": "RECOMMENDED",
                        "aspectEnabledForVariations": False,
                        "aspectApplicableTo": ["PRODUCT"],
                    },
                    "aspectValues": [
                        {"localizedValue": "A"},
                        {"localizedValue": "B"},
                        {"localizedValue": "C"},
                    ],
                },
                {
                    "localizedAspectName": "Detailed Description",
                    "aspectConstraint": {
                        "aspectDataType": "STRING",
                        "aspectMode": "FREE_TEXT",
                        "aspectRequired": False,
                        "aspectUsage": "OPTIONAL",
                        "aspectEnabledForVariations": False,
                        "aspectApplicableTo": ["PRODUCT"],
                        "aspectMaxLength": 1000,
                    },
                    "aspectValues": [],
                },
                {
                    "localizedAspectName": "Material",
                    "aspectConstraint": {
                        "aspectDataType": "STRING",
                        "aspectMode": "FREE_TEXT",
                        "aspectRequired": False,
                        "aspectUsage": "OPTIONAL",
                        "aspectEnabledForVariations": False,
                        "aspectApplicableTo": ["PRODUCT"],
                        "aspectMaxLength": 200,
                    },
                },
                {
                    "localizedAspectName": "Voltage",
                    "aspectConstraint": {
                        "aspectDataType": "STRING",
                        "aspectMode": "FREE_TEXT",
                        "aspectRequired": False,
                        "aspectUsage": "OPTIONAL",
                        "aspectEnabledForVariations": False,
                        "aspectApplicableTo": ["PRODUCT"],
                        "aspectAdvancedDataType": "NUMERIC_RANGE",
                    },
                },
                {
                    "localizedAspectName": "Screen Size",
                    "aspectConstraint": {
                        "aspectDataType": "NUMBER",
                        "aspectFormat": "double",
                        "aspectMode": "FREE_TEXT",
                        "aspectRequired": False,
                        "aspectUsage": "OPTIONAL",
                        "aspectEnabledForVariations": False,
                        "aspectApplicableTo": ["PRODUCT"],
                    },
                },
                {
                    "localizedAspectName": "Memory",
                    "aspectConstraint": {
                        "aspectDataType": "NUMBER",
                        "aspectFormat": "int32",
                        "aspectMode": "FREE_TEXT",
                        "aspectRequired": False,
                        "aspectUsage": "OPTIONAL",
                        "aspectEnabledForVariations": False,
                        "aspectApplicableTo": ["PRODUCT"],
                    },
                },
                {
                    "localizedAspectName": "Release Date",
                    "aspectConstraint": {
                        "aspectDataType": "DATE",
                        "aspectFormat": "YYYYMMDD",
                        "aspectMode": "FREE_TEXT",
                        "aspectRequired": False,
                        "aspectUsage": "OPTIONAL",
                        "aspectEnabledForVariations": False,
                        "aspectApplicableTo": ["PRODUCT"],
                    },
                },
                {
                    "localizedAspectName": "Warranty Expiration",
                    "aspectConstraint": {
                        "aspectDataType": "DATE",
                        "aspectFormat": "YYYYMMDDHHMMSS",
                        "aspectMode": "FREE_TEXT",
                        "aspectRequired": False,
                        "aspectUsage": "OPTIONAL",
                        "aspectEnabledForVariations": False,
                        "aspectApplicableTo": ["PRODUCT"],
                    },
                },
                {
                    "localizedAspectName": "Item Only",
                    "aspectConstraint": {
                        "aspectDataType": "STRING",
                        "aspectMode": "FREE_TEXT",
                        "aspectApplicableTo": ["ITEM"],
                    },
                },
            ]
        }

    def test_run_creates_remote_models_with_expected_mapping(self) -> None:
        _ensure_stubbed_ebay_rest()

        from sales_channels.integrations.ebay.factories.sales_channels.full_schema import (
            EbayProductTypeRuleFactory,
        )

        dummy_api = _DummyEbayAPI(
            category_response=self._build_category_response(),
            aspects_response=self._build_aspects_response(),
        )

        with patch.object(EbayProductTypeRuleFactory, "get_api", return_value=dummy_api):
            factory = EbayProductTypeRuleFactory(
                sales_channel=self.sales_channel,
                view=self.view,
                category_id="3197",
                category_tree_id="123",
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

