"""Tests for Shein product import behavior."""

from core.tests import TestCase
from model_bakery import baker

from products.models import ConfigurableVariation, Product
from properties.models import ProductProperty, Property, PropertySelectValue
from sales_channels.integrations.shein.factories.imports.products import (
    SheinProductsImportProcessor,
)
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinProduct,
    SheinProductCategory,
    SheinProperty,
    SheinPropertySelectValue,
    SheinSalesChannel,
    SheinSalesChannelView,
)
from sales_channels.integrations.shein.models.imports import SheinSalesChannelImport
from sales_channels.models import SalesChannelViewAssign


class SheinProductImportTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            sync_contents=False,
            sync_ean_codes=False,
            sync_prices=False,
        )
        self.import_process = baker.make(
            SheinSalesChannelImport,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            type=SheinSalesChannelImport.TYPE_PRODUCTS,
        )

    def test_configurable_import_generates_parent_sku_and_links_variations(self) -> None:
        baker.make(
            SheinCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="20039882",
            product_type_remote_id="2147503175",
            is_leaf=True,
        )
        payload = {
            "spuName": "a250611520068",
            "categoryId": 20039882,
            "productTypeId": 2147503175,
            "skcInfoList": [
                {
                    "attributeId": 2147484187,
                    "attributeValueId": 2147488295,
                    "skcName": "sa25061152006814133",
                    "shelfStatusInfoList": [
                        {
                            "siteAbbr": "shein-us",
                            "shelfStatus": 0,
                        }
                    ],
                    "skuInfoList": [
                        {
                            "skuCode": "I04hto929j3h",
                            "supplierSku": "ppp0001",
                        }
                    ],
                },
                {
                    "attributeId": 2147484187,
                    "attributeValueId": 2147488294,
                    "skcName": "sa25061152006824283",
                    "shelfStatusInfoList": [
                        {
                            "siteAbbr": "shein-us",
                            "shelfStatus": 0,
                        }
                    ],
                    "skuInfoList": [
                        {
                            "skuCode": "I04hto92an8k",
                            "supplierSku": "PPPP0002",
                        }
                    ],
                },
            ],
        }

        processor = SheinProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor.process_product_item(product_data=payload)

        parent = Product.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
        ).first()
        self.assertIsNotNone(parent)
        parent_sku = parent.sku if parent else None
        self.assertNotIn(parent_sku, {"ppp0001", "PPPP0002"})

        variations = Product.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            sku__in=["ppp0001", "PPPP0002"],
        )
        self.assertEqual(variations.count(), 2)
        linked_skus = set(
            ConfigurableVariation.objects.filter(parent=parent).values_list(
                "variation__sku",
                flat=True,
            )
        )
        self.assertSetEqual(linked_skus, {"ppp0001", "PPPP0002"})

        categories = SheinProductCategory.objects.filter(
            sales_channel=self.sales_channel,
            product__sku__in=[parent_sku, "ppp0001", "PPPP0002"],
        )
        self.assertEqual(categories.count(), 3)
        remote_skus = set(
            SheinProduct.objects.filter(
                sales_channel=self.sales_channel,
                remote_sku__in=["ppp0001", "PPPP0002"],
            ).values_list("remote_sku", flat=True)
        )
        self.assertSetEqual(remote_skus, {"ppp0001", "PPPP0002"})

    def test_configurable_import_copies_spu_attributes_to_variations(self) -> None:
        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=local_property,
        )
        shein_property = baker.make(
            SheinProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=local_property,
            remote_id="2147484226",
            type=Property.TYPES.SELECT,
        )
        baker.make(
            SheinPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=shein_property,
            local_instance=local_value,
            remote_id="2147488744",
            value="0-3years",
        )

        payload = {
            "spuName": "d250703110342",
            "productTypeId": 2147503259,
            "productAttributeInfoList": [
                {
                    "attributeId": 2147484226,
                    "attributeValueId": 2147488744,
                    "attributeValueMultiList": [
                        {"attributeValueName": "0-3years", "language": "en"}
                    ],
                }
            ],
            "skcInfoList": [
                {
                    "attributeId": 2147484187,
                    "attributeValueId": 2147488077,
                    "skcName": "sd25070311034260014",
                    "skuInfoList": [
                        {"skuCode": "I0zvxmgz9my", "supplierSku": "BOFFLE-WOODEN-VAR-1"}
                    ],
                },
                {
                    "attributeId": 2147484187,
                    "attributeValueId": 739,
                    "skcName": "sd25070311034285141",
                    "skuInfoList": [
                        {"skuCode": "I010pm1kd0bm", "supplierSku": "BOFFLE-WOODEN-VAR-2"}
                    ],
                },
            ],
        }

        processor = SheinProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor.process_product_item(product_data=payload)

        for sku in ("BOFFLE-WOODEN-VAR-1", "BOFFLE-WOODEN-VAR-2"):
            product = Product.objects.get(
                multi_tenant_company=self.multi_tenant_company,
                sku=sku,
            )
            prop = ProductProperty.objects.get(
                product=product,
                property=local_property,
            )
            self.assertEqual(prop.value_select_id, local_value.id)

    def test_import_sets_view_assign_link(self) -> None:
        view = baker.make(
            SheinSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="shein-us",
            name="Shein US",
            url="https://us.shein.com",
        )
        payload = {
            "spuName": "a250623501429",
            "categoryId": 20039882,
            "productTypeId": 2147503175,
            "skcInfoList": [
                {
                    "skcName": "sa25062350142989502",
                    "shelfStatusInfoList": [
                        {
                            "siteAbbr": "shein-us",
                            "shelfStatus": 0,
                            "link": "https://us.shein.com/Product-Name-New-Eu-p-54645646511380-cat-4913127300.html",
                        }
                    ],
                    "skuInfoList": [
                        {
                            "skuCode": "I4znql6gdv6",
                            "supplierSku": "SHORTS-1",
                        }
                    ],
                }
            ],
        }

        processor = SheinProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor.process_product_item(product_data=payload)

        assign = SalesChannelViewAssign.objects.get(
            product__sku="SHORTS-1",
            sales_channel_view=view,
        )
        self.assertEqual(
            assign.link,
            "https://us.shein.com/Product-Name-New-Eu-p-54645646511380-cat-4913127300.html",
        )

    def test_handle_variations_ignores_duplicate_category_assignment(self) -> None:
        class DummyImportInstance:
            def __init__(self, *, remote_instance):
                self.remote_instance = remote_instance

        category = baker.make(
            SheinCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="20039882",
            product_type_remote_id="2147503175",
            is_leaf=True,
        )
        local_parent = baker.make(Product, multi_tenant_company=self.multi_tenant_company, type=Product.CONFIGURABLE)
        local_variation = baker.make(Product, multi_tenant_company=self.multi_tenant_company)
        remote_parent = baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=local_parent,
        )
        remote_variation = baker.make(
            SheinProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=local_variation,
        )
        baker.make(
            SheinProductCategory,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=local_parent,
            remote_id=category.remote_id,
            product_type_remote_id=category.product_type_remote_id,
        )
        other_company = baker.make(type(self.multi_tenant_company))
        baker.make(
            SheinProductCategory,
            multi_tenant_company=other_company,
            sales_channel=self.sales_channel,
            product=local_variation,
            remote_id=category.remote_id,
            product_type_remote_id=category.product_type_remote_id,
        )

        processor = SheinProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor.handle_variations(
            import_instance=DummyImportInstance(remote_instance=remote_variation),
            parent_sku="parent-sku",
            parent_remote=remote_parent,
        )

        self.assertEqual(
            SheinProductCategory.objects.filter(
                sales_channel=self.sales_channel,
                product=local_variation,
            ).count(),
            1,
        )
