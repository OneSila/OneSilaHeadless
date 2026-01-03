from types import SimpleNamespace
from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker

from currencies.models import Currency
from eancodes.models import EanCode
from products.models import ConfigurableVariation, Product, ProductTranslation
from properties.models import (
    ProductPropertiesRule,
    ProductPropertiesRuleItem,
    ProductProperty,
    ProductPropertyTextTranslation,
    Property,
    PropertySelectValue,
)
from sales_channels.integrations.shein.factories.products import (
    SheinProductCreateFactory,
    SheinProductUpdateFactory,
)
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinProductType,
    SheinProductTypeItem,
    SheinProperty,
    SheinPropertySelectValue,
    SheinProduct,
    SheinInternalProperty,
    SheinInternalPropertyOption,
    SheinRemoteLanguage,
    SheinSalesChannel,
    SheinSalesChannelView,
)
from sales_channels.integrations.shein.models.sales_channels import SheinRemoteCurrency
from sales_channels.integrations.shein.exceptions import SheinConfiguratorAttributesLimitError
from sales_channels.models import SalesChannelViewAssign
from sales_prices.models import SalesPrice


class SheinProductPayloadFactoryTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.test",
            remote_id="SC-1",
            starting_stock=5,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            active=True,
            sku="SKU-1",
        )
        self.remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_id="SPU-1",
            remote_sku="SKU-1",
            spu_name="SPU-1",
        )
        self.view = SheinSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="shein-fr",
            is_default=True,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
        )
        currency = Currency.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            iso_code="EUR",
            name="Euro",
            symbol="€",
        )
        SheinRemoteCurrency.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_code="EUR",
            local_instance=currency,
        )

        self.product_type_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True,
            defaults={"type": Property.TYPES.SELECT},
        )

    def _create_product_type_rule(self, product: Product, *, remote_id: str = "TYPE-1", category_id: str = "CAT-1"):
        product_type_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property,
        )
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=self.product_type_property,
            value_select=product_type_value,
        )
        rule = ProductPropertiesRule.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=product_type_value,
            sales_channel=self.sales_channel,
        )
        shein_product_type = SheinProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id=remote_id,
            category_id=category_id,
            local_instance=rule,
        )
        return rule, shein_product_type

    def _link_shein_property(self, *, property_obj: Property, shein_product_type: SheinProductType, remote_id: str, is_main: bool):
        shein_prop = SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id=remote_id,
            local_instance=property_obj,
            type=property_obj.type,
        )
        shein_type_item = SheinProductTypeItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type=shein_product_type,
            property=shein_prop,
            requirement=SheinProductTypeItem.Requirement.REQUIRED,
            attribute_type=SheinProductTypeItem.AttributeType.SALES,
            is_main_attribute=is_main,
        )
        return shein_prop, shein_type_item

    def _link_shein_value(self, *, shein_property: SheinProperty, local_value: PropertySelectValue, remote_value: str):
        SheinPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_property=shein_property,
            local_instance=local_value,
            remote_id=remote_value,
            value=local_value.value or "",
        )

    def _ensure_supplier_code_property(self) -> Property:
        supplier_property = getattr(self, "_supplier_code_property", None)
        if supplier_property is not None:
            return supplier_property

        supplier_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )
        SheinInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="supplier_code",
            name="Supplier code",
            type=Property.TYPES.TEXT,
            payload_field="supplier_code",
            local_instance=supplier_property,
        )
        self._supplier_code_property = supplier_property
        return supplier_property

    def _assign_supplier_code(self, *, product: Product, value: str) -> None:
        supplier_property = self._ensure_supplier_code_property()
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=supplier_property,
        )
        ProductPropertyTextTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_property=product_property,
            language=self.multi_tenant_company.language,
            value_text=value,
        )

    def _create_variation(
        self,
        *,
        parent: Product,
        sku: str,
        color_property: Property,
        color_value: PropertySelectValue,
        size_property: Property | None = None,
        size_value: PropertySelectValue | None = None,
    ) -> Product:
        variation = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            active=True,
            sku=sku,
        )
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=variation,
            property=color_property,
            value_select=color_value,
        )
        if size_property and size_value:
            ProductProperty.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=variation,
                property=size_property,
                value_select=size_value,
            )
        ConfigurableVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=parent,
            variation=variation,
        )
        return variation

    def test_build_translations_prefers_sales_channel_and_filters_languages(self) -> None:
        SheinRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance="en",
            remote_code="en",
        )
        SheinRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance="fr",
            remote_code="fr",
        )
        category = SheinCategory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="CAT-DEFAULT",
            default_language="fr",
            name="Category",
            raw_data={},
        )

        ProductTranslation.objects.create(
            product=self.product,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            language="en",
            name="Channel EN",
            description="Channel EN desc",
        )
        ProductTranslation.objects.create(
            product=self.product,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=None,
            language="en",
            name="Default EN",
            description="Default EN desc",
        )
        ProductTranslation.objects.create(
            product=self.product,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=None,
            language="fr",
            name="Default FR",
            description="Default FR desc",
        )
        ProductTranslation.objects.create(
            product=self.product,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            language="es",
            name="Ignored ES",
            description="Ignored ES desc",
        )

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            get_value_only=True,
        )
        factory.selected_category_id = category.remote_id
        self.assertEqual(factory._get_default_language(), "fr")
        factory._build_translations()

        self.assertCountEqual(
            factory.multi_language_name_list,
            [
                {"language": "en", "name": "Channel EN"},
                {"language": "fr", "name": "Default FR"},
            ],
        )
        self.assertCountEqual(
            factory.multi_language_desc_list,
            [
                {"language": "en", "name": "Channel EN desc"},
                {"language": "fr", "name": "Default FR desc"},
            ],
        )

    def test_build_translations_falls_back_when_channel_description_blank(self) -> None:
        SheinRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance="en",
            remote_code="en",
        )

        ProductTranslation.objects.create(
            product=self.product,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            language="en",
            name="Channel EN",
            description="<p><br></p>",
        )
        ProductTranslation.objects.create(
            product=self.product,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=None,
            language="en",
            name="Default EN",
            description="Default EN desc",
        )

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            get_value_only=True,
        )
        factory._build_translations()

        self.assertCountEqual(
            factory.multi_language_name_list,
            [{"language": "en", "name": "Channel EN"}],
        )
        self.assertCountEqual(
            factory.multi_language_desc_list,
            [{"language": "en", "name": "Default EN desc"}],
        )

    def test_shein_build_sku_list_includes_supplier_barcode_and_package_type(self) -> None:
        self._assign_supplier_code(product=self.product, value="SUP-1")
        EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            ean_code="123-456-7890123",
        )

        package_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        package_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=package_property,
        )
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=package_property,
            value_select=package_value,
        )
        internal_property = SheinInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="package_type",
            name="Package type",
            type=Property.TYPES.SELECT,
            payload_field="package_type",
            local_instance=package_property,
        )
        SheinInternalPropertyOption.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_property=internal_property,
            sales_channel=self.sales_channel,
            local_instance=package_value,
            value="3",
            label="Hard packaging",
            sort_order=0,
            raw_data={},
        )

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        sku = factory._build_sku_list(assigns=[])[0]

        self.assertEqual(sku["supplier_barcode"]["barcode"], "1234567890123")
        self.assertEqual(sku["supplier_barcode"]["barcode_type"], "EAN")
        self.assertEqual(sku["package_type"], "3")
        self.assertEqual(sku["supplier_code"], "SUP-1")

    def test_shein_build_sku_list_includes_quantity_info(self) -> None:
        self._assign_supplier_code(product=self.product, value="SUP-QTY-1")
        unit_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        unit_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=unit_property,
        )
        quantity_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.INT,
        )
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=unit_property,
            value_select=unit_value,
        )
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=quantity_property,
            value_int=3,
        )
        unit_internal = SheinInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="quantity_info__unit",
            name="Quantity unit",
            type=Property.TYPES.SELECT,
            payload_field="quantity_unit",
            local_instance=unit_property,
        )
        SheinInternalPropertyOption.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_property=unit_internal,
            sales_channel=self.sales_channel,
            local_instance=unit_value,
            value="1",
            label="Piece",
            sort_order=0,
            raw_data={},
        )
        SheinInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="quantity_info__quantity",
            name="Quantity",
            type=Property.TYPES.INT,
            payload_field="quantity",
            local_instance=quantity_property,
        )

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        sku = factory._build_sku_list(assigns=[])[0]

        self.assertEqual(
            sku["quantity_info"],
            {"quantity_type": 2, "quantity_unit": 1, "quantity": 3},
        )
        fill_configuration = factory._build_fill_configuration_info(
            package_type=None,
            filled_quantity_to_sku=factory.has_quantity_info,
        )
        self.assertEqual(fill_configuration, {"filled_quantity_to_sku": True})

    def test_shein_create_payload_omits_spu_name_and_includes_site_list(self) -> None:
        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.remote_rule = type("Rule", (), {"category_id": "1727", "remote_id": "1080"})()

        with (
            patch.object(SheinProductCreateFactory, "_build_property_payloads"),
            patch.object(SheinProductCreateFactory, "_build_prices"),
            patch.object(SheinProductCreateFactory, "_build_media"),
            patch.object(SheinProductCreateFactory, "_build_translations"),
            patch.object(SheinProductCreateFactory, "_build_skc_list"),
        ):
            payload = factory.build_payload()

        self.assertNotIn("spu_name", payload)
        self.assertIn("site_list", payload)

    def test_shein_update_payload_includes_spu_name_and_omits_site_list(self) -> None:
        factory = SheinProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.remote_rule = type("Rule", (), {"category_id": "1727", "remote_id": "1080"})()

        with (
            patch.object(SheinProductUpdateFactory, "_build_property_payloads"),
            patch.object(SheinProductUpdateFactory, "_build_prices"),
            patch.object(SheinProductUpdateFactory, "_build_media"),
            patch.object(SheinProductUpdateFactory, "_build_translations"),
            patch.object(SheinProductUpdateFactory, "_build_skc_list"),
        ):
            payload = factory.build_payload()

        self.assertEqual(payload["spu_name"], "SPU-1")
        self.assertEqual(payload["brand_code"], "")
        self.assertNotIn("site_list", payload)
        self.assertNotIn("sale_attribute_list", payload)

    def test_shein_update_without_spu_name_uses_create_payload(self) -> None:
        remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_id="SPU-1",
            remote_sku="SKU-1",
        )
        factory = SheinProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.remote_rule = type("Rule", (), {"category_id": "1727", "remote_id": "1080"})()

        def fake_property_payloads(self):
            self.sale_attribute_list = [{"attribute_id": 1, "attribute_value_id": 2}]

        with (
            patch.object(SheinProductUpdateFactory, "_build_property_payloads", autospec=True, side_effect=fake_property_payloads),
            patch.object(SheinProductUpdateFactory, "_build_prices"),
            patch.object(SheinProductUpdateFactory, "_build_media"),
            patch.object(SheinProductUpdateFactory, "_build_translations"),
            patch.object(SheinProductUpdateFactory, "_build_skc_list"),
        ):
            payload = factory.build_payload()

        self.assertNotIn("spu_name", payload)
        self.assertIn("site_list", payload)
        self.assertIn("sale_attribute_list", payload)

    def test_shein_configurable_payload_builds_skc_and_sku_lists_with_single_attribute(self) -> None:
        parent = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            active=True,
            sku="PARENT-1",
        )
        rule, shein_product_type = self._create_product_type_rule(parent)

        color_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        red = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=color_property)
        blue = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=color_property)
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=rule,
            property=color_property,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            sort_order=0,
        )

        shein_color, _ = self._link_shein_property(
            property_obj=color_property,
            shein_product_type=shein_product_type,
            remote_id="COLOR",
            is_main=True,
        )
        self._link_shein_value(shein_property=shein_color, local_value=red, remote_value="R-1")
        self._link_shein_value(shein_property=shein_color, local_value=blue, remote_value="B-1")

        red_variation = self._create_variation(
            parent=parent,
            sku="RED-1",
            color_property=color_property,
            color_value=red,
        )
        blue_variation = self._create_variation(
            parent=parent,
            sku="BLUE-1",
            color_property=color_property,
            color_value=blue,
        )
        self._assign_supplier_code(product=red_variation, value="SUP-RED-A")
        self._assign_supplier_code(product=blue_variation, value="SUP-BLUE-A")

        remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_sku=parent.sku,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=parent,
            sales_channel_view=self.view,
            remote_product=remote_product,
        )

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_instance=remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.remote_rule = type("Rule", (), {"category_id": shein_product_type.category_id, "remote_id": shein_product_type.remote_id})()

        with (
            patch.object(SheinProductCreateFactory, "_build_property_payloads"),
            patch.object(SheinProductCreateFactory, "_build_prices"),
            patch.object(SheinProductCreateFactory, "_build_media"),
            patch.object(SheinProductCreateFactory, "_build_translations"),
        ):
            payload = factory.build_payload()

        skc_list = payload["skc_list"]
        self.assertEqual(len(skc_list), 2)

        primary_values = {skc["sale_attribute"]["attribute_value_id"] for skc in skc_list}
        self.assertSetEqual(primary_values, {"R-1", "B-1"})

        all_skus = [sku["supplier_sku"] for skc in skc_list for sku in skc["sku_list"]]
        self.assertCountEqual(all_skus, [red_variation.sku, blue_variation.sku])
        for skc in skc_list:
            for sku in skc["sku_list"]:
                self.assertNotIn("sale_attribute_list", sku)

    def test_shein_configurable_payload_builds_secondary_sale_attributes(self) -> None:
        parent = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            active=True,
            sku="PARENT-2",
        )
        rule, shein_product_type = self._create_product_type_rule(parent)

        color_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        size_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        red = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=color_property)
        blue = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=color_property)
        small = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=size_property)
        large = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=size_property)

        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=rule,
            property=color_property,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            sort_order=0,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=rule,
            property=size_property,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            sort_order=1,
        )

        shein_color, _ = self._link_shein_property(
            property_obj=color_property,
            shein_product_type=shein_product_type,
            remote_id="COLOR",
            is_main=True,
        )
        shein_size, _ = self._link_shein_property(
            property_obj=size_property,
            shein_product_type=shein_product_type,
            remote_id="SIZE",
            is_main=False,
        )
        self._link_shein_value(shein_property=shein_color, local_value=red, remote_value="R-1")
        self._link_shein_value(shein_property=shein_color, local_value=blue, remote_value="B-1")
        self._link_shein_value(shein_property=shein_size, local_value=small, remote_value="S-1")
        self._link_shein_value(shein_property=shein_size, local_value=large, remote_value="L-1")

        red_small = self._create_variation(
            parent=parent,
            sku="RED-S",
            color_property=color_property,
            color_value=red,
            size_property=size_property,
            size_value=small,
        )
        blue_large = self._create_variation(
            parent=parent,
            sku="BLUE-L",
            color_property=color_property,
            color_value=blue,
            size_property=size_property,
            size_value=large,
        )
        self._assign_supplier_code(product=red_small, value="SUP-RED-B")
        self._assign_supplier_code(product=blue_large, value="SUP-BLUE-B")

        remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_sku=parent.sku,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=parent,
            sales_channel_view=self.view,
            remote_product=remote_product,
        )

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_instance=remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.remote_rule = type("Rule", (), {"category_id": shein_product_type.category_id, "remote_id": shein_product_type.remote_id})()

        with (
            patch.object(SheinProductCreateFactory, "_build_property_payloads"),
            patch.object(SheinProductCreateFactory, "_build_prices"),
            patch.object(SheinProductCreateFactory, "_build_media"),
            patch.object(SheinProductCreateFactory, "_build_translations"),
        ):
            payload = factory.build_payload()

        skc_list = payload["skc_list"]
        self.assertEqual(len(skc_list), 2)

        for skc in skc_list:
            sku_entry = skc["sku_list"][0]
            self.assertIn("sale_attribute_list", sku_entry)
            secondary = sku_entry["sale_attribute_list"][0]
            self.assertEqual(secondary["attribute_id"], "SIZE")
            self.assertIn(secondary["attribute_value_id"], {"S-1", "L-1"})

        sku_values = {skc["sale_attribute"]["attribute_value_id"] for skc in skc_list}
        self.assertSetEqual(sku_values, {"R-1", "B-1"})
        self.assertCountEqual(
            [sku["supplier_sku"] for skc in skc_list for sku in skc["sku_list"]],
            [red_small.sku, blue_large.sku],
        )

    def test_shein_raises_when_more_than_three_configurator_attributes(self) -> None:
        parent = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            active=True,
            sku="PARENT-3",
        )
        rule, shein_product_type = self._create_product_type_rule(parent)

        prop_a = baker.make(Property, multi_tenant_company=self.multi_tenant_company, type=Property.TYPES.SELECT)
        prop_b = baker.make(Property, multi_tenant_company=self.multi_tenant_company, type=Property.TYPES.SELECT)
        prop_c = baker.make(Property, multi_tenant_company=self.multi_tenant_company, type=Property.TYPES.SELECT)
        prop_d = baker.make(Property, multi_tenant_company=self.multi_tenant_company, type=Property.TYPES.SELECT)
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=rule,
            property=prop_a,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            sort_order=0,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=rule,
            property=prop_b,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            sort_order=1,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=rule,
            property=prop_c,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            sort_order=2,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=rule,
            property=prop_d,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            sort_order=3,
        )

        shein_type = shein_product_type
        for idx, property_obj in enumerate([prop_a, prop_b, prop_c, prop_d], start=1):
            shein_prop, _ = self._link_shein_property(
                property_obj=property_obj,
                shein_product_type=shein_type,
                remote_id=f"ATTR-{idx}",
                is_main=idx == 1,
            )
            for value_idx in range(2):
                local_value = baker.make(
                    PropertySelectValue,
                    multi_tenant_company=self.multi_tenant_company,
                    property=property_obj,
                )
                self._link_shein_value(
                    shein_property=shein_prop,
                    local_value=local_value,
                    remote_value=f"{idx}-{value_idx}",
                )

        values_a = list(PropertySelectValue.objects.filter(property=prop_a)[:2])
        values_b = list(PropertySelectValue.objects.filter(property=prop_b)[:2])
        values_c = list(PropertySelectValue.objects.filter(property=prop_c)[:2])
        values_d = list(PropertySelectValue.objects.filter(property=prop_d)[:2])

        variation_one = self._create_variation(
            parent=parent,
            sku="A1",
            color_property=prop_a,
            color_value=values_a[0],
            size_property=prop_b,
            size_value=values_b[0],
        )
        variation_two = self._create_variation(
            parent=parent,
            sku="A2",
            color_property=prop_a,
            color_value=values_a[1],
            size_property=prop_b,
            size_value=values_b[1],
        )
        # third and fourth axes differ
        for variation, val in zip([variation_one, variation_two], values_c):
            ProductProperty.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=variation,
                property=prop_c,
                value_select=val,
            )
        values_d = list(PropertySelectValue.objects.filter(property=prop_d)[:2])
        for variation, val in zip([variation_one, variation_two], values_d):
            ProductProperty.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=variation,
                property=prop_d,
                value_select=val,
            )

        remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_sku=parent.sku,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=parent,
            sales_channel_view=self.view,
            remote_product=remote_product,
        )

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_instance=remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.remote_rule = type("Rule", (), {"category_id": shein_product_type.category_id, "remote_id": shein_product_type.remote_id})()

        with (
            patch.object(SheinProductCreateFactory, "_build_property_payloads"),
            patch.object(SheinProductCreateFactory, "_build_prices"),
            patch.object(SheinProductCreateFactory, "_build_media"),
            patch.object(SheinProductCreateFactory, "_build_translations"),
        ):
            with self.assertRaises(SheinConfiguratorAttributesLimitError):
                factory.build_payload()

    def test_shein_simple_payload_matches_expected(self) -> None:
        image_info = {
            "image_info_list": [
                {"image_sort": 1, "image_type": 1, "image_url": "https://img.example.com/1.jpg"}
            ]
        }
        product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            active=True,
            sku="SIMPLE-1",
        )
        self._assign_supplier_code(product=product, value="SUP-SIMPLE")
        remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_sku=product.sku,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=product,
            sales_channel_view=self.view,
            remote_product=remote_product,
        )

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_instance=remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.remote_rule = type("Rule", (), {"category_id": "CAT-1", "remote_id": "TYPE-1"})()

        def fake_property_payloads(self):
            self.sale_attribute = {"attribute_id": "COLOR", "attribute_value_id": "RED"}

        with (
            patch.object(SheinProductCreateFactory, "_build_property_payloads", autospec=True, side_effect=fake_property_payloads),
            patch.object(SheinProductCreateFactory, "_build_prices"),
            patch.object(SheinProductCreateFactory, "_build_media", autospec=True, side_effect=lambda self: setattr(self, "image_info", image_info)),
            patch.object(SheinProductCreateFactory, "_build_translations"),
        ):
            payload = factory.build_payload()

        expected = {
            "category_id": "CAT-1",
            "product_type_id": "TYPE-1",
            "supplier_code": "SUP-SIMPLE",
            "source_system": "openapi",
            "site_list": [
                {"main_site": "shein", "sub_site_list": ["shein-fr"]},
            ],
            "sale_attribute": {"attribute_id": "COLOR", "attribute_value_id": "RED"},
            "skc_list": [
                {
                    "shelf_way": "1",
                    "image_info": image_info,
                    "sale_attribute": {"attribute_id": "COLOR", "attribute_value_id": "RED"},
                    "supplier_code": "SUP-SIMPLE",
                    "sku_list": [
                        {
                            "mall_state": 1,
                            "supplier_sku": product.sku,
                            "supplier_code": "SUP-SIMPLE",
                            "stop_purchase": 1,
                            "height": "10.0",
                            "length": "10.0",
                            "width": "10.0",
                            "weight": 10,
                            "stock_info_list": [{"inventory_num": 5}],
                        }
                    ],
                }
            ],
        }
        self.assertEqual(payload, expected, self._format_payload_debug(payload, expected))

    def test_shein_configurable_payload_with_color_only(self) -> None:
        image_info = {
            "image_info_list": [
                {"image_sort": 1, "image_type": 1, "image_url": "https://img.example.com/1.jpg"}
            ]
        }
        parent = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            active=True,
            sku="CONF-COLOR",
        )
        rule, shein_product_type = self._create_product_type_rule(
            parent,
            remote_id="TYPE-2",
            category_id="CAT-2",
        )
        SheinCategory.objects.create(
            remote_id="CAT-2",
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            support_sale_attribute_sort=True,
        )
        color_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        red = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=color_property)
        blue = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=color_property)
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=rule,
            property=color_property,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            sort_order=0,
        )

        shein_color, _ = self._link_shein_property(
            property_obj=color_property,
            shein_product_type=shein_product_type,
            remote_id="COLOR",
            is_main=True,
        )
        self._link_shein_value(shein_property=shein_color, local_value=red, remote_value="RED-1")
        self._link_shein_value(shein_property=shein_color, local_value=blue, remote_value="BLUE-1")

        red_variation = self._create_variation(
            parent=parent,
            sku="CONF-RED",
            color_property=color_property,
            color_value=red,
        )
        blue_variation = self._create_variation(
            parent=parent,
            sku="CONF-BLUE",
            color_property=color_property,
            color_value=blue,
        )
        self._assign_supplier_code(product=red_variation, value="SUP-RED-1")
        self._assign_supplier_code(product=blue_variation, value="SUP-BLUE-1")

        remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_sku=parent.sku,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=parent,
            sales_channel_view=self.view,
            remote_product=remote_product,
        )

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_instance=remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.remote_rule = type("Rule", (), {"category_id": shein_product_type.category_id, "remote_id": shein_product_type.remote_id})()
        factory.selected_category_id = shein_product_type.category_id
        factory.selected_product_type_id = shein_product_type.remote_id
        factory.rule = rule

        with (
            patch.object(
                SheinProductCreateFactory,
                "_build_media",
                autospec=True,
                side_effect=lambda self: setattr(self, "image_info", image_info),
            ),
            patch.object(
                SheinProductCreateFactory,
                "_build_image_info_for_product",
                autospec=True,
                return_value=image_info,
            ),
        ):
            payload = factory.build_payload()

        skc_list = sorted(payload["skc_list"], key=lambda skc: skc["sale_attribute"]["attribute_value_id"])
        payload["skc_list"] = skc_list
        expected_skc = [
            {
                "shelf_way": "1",
                "image_info": image_info,
                "sale_attribute": {"attribute_id": "COLOR", "attribute_value_id": "BLUE-1"},
                "supplier_code": "SUP-BLUE-1",
                "sku_list": [
                    {
                        "mall_state": 1,
                        "supplier_sku": blue_variation.sku,
                        "supplier_code": "SUP-BLUE-1",
                        "stop_purchase": 1,
                        "height": "10.0",
                        "length": "10.0",
                        "width": "10.0",
                        "weight": 10,
                        "stock_info_list": [{"inventory_num": 5}],
                    }
                ],
            },
            {
                "shelf_way": "1",
                "image_info": image_info,
                "sale_attribute": {"attribute_id": "COLOR", "attribute_value_id": "RED-1"},
                "supplier_code": "SUP-RED-1",
                "sku_list": [
                    {
                        "mall_state": 1,
                        "supplier_sku": red_variation.sku,
                        "supplier_code": "SUP-RED-1",
                        "stop_purchase": 1,
                        "height": "10.0",
                        "length": "10.0",
                        "width": "10.0",
                        "weight": 10,
                        "stock_info_list": [{"inventory_num": 5}],
                    }
                ],
            },
        ]

        expected = {
            "category_id": "CAT-2",
            "product_type_id": "TYPE-2",
            "source_system": "openapi",
            "site_list": [{"main_site": "shein", "sub_site_list": ["shein-fr"]}],
            "sale_attribute_sort_list": [
                {
                    "attribute_id": "COLOR",
                    "in_order_attribute_value_id_list": ["RED-1", "BLUE-1"],
                }
            ],
            "skc_list": expected_skc,
        }
        self.assertEqual(payload, expected, self._format_payload_debug(payload, expected))

    def test_shein_configurable_payload_includes_sku_prices(self) -> None:
        parent = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            active=True,
            sku="CONF-PRICE",
        )
        rule, shein_product_type = self._create_product_type_rule(
            parent,
            remote_id="TYPE-PRICE",
            category_id="CAT-PRICE",
        )
        color_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        red = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=color_property)
        blue = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=color_property)
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=rule,
            property=color_property,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            sort_order=0,
        )

        shein_color, _ = self._link_shein_property(
            property_obj=color_property,
            shein_product_type=shein_product_type,
            remote_id="COLOR",
            is_main=True,
        )
        self._link_shein_value(shein_property=shein_color, local_value=red, remote_value="RED-1")
        self._link_shein_value(shein_property=shein_color, local_value=blue, remote_value="BLUE-1")

        red_variation = self._create_variation(
            parent=parent,
            sku="CONF-PRICE-RED",
            color_property=color_property,
            color_value=red,
        )
        blue_variation = self._create_variation(
            parent=parent,
            sku="CONF-PRICE-BLUE",
            color_property=color_property,
            color_value=blue,
        )

        currency = Currency.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            iso_code="USD",
            name="US Dollar",
            symbol="$",
        )
        SheinRemoteCurrency.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_code="USD",
            local_instance=currency,
            sales_channel_view=self.view,
        )
        SalesPrice.objects.update_or_create(
            product=red_variation,
            currency=currency,
            multi_tenant_company=self.multi_tenant_company,
            defaults={"price": 25},
        )
        SalesPrice.objects.update_or_create(
            product=blue_variation,
            currency=currency,
            multi_tenant_company=self.multi_tenant_company,
            defaults={"price": 30},
        )

        remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_sku=parent.sku,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=parent,
            sales_channel_view=self.view,
            remote_product=remote_product,
        )

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_instance=remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.remote_rule = type("Rule", (), {"category_id": shein_product_type.category_id, "remote_id": shein_product_type.remote_id})()
        factory.selected_category_id = shein_product_type.category_id
        factory.selected_product_type_id = shein_product_type.remote_id
        factory.rule = rule

        payload = factory.build_payload()

        price_entries = [
            sku.get("price_info_list")
            for skc in payload.get("skc_list", [])
            for sku in skc.get("sku_list", [])
        ]
        self.assertTrue(any(entry for entry in price_entries))

    def test_shein_configurable_payload_with_color_and_size(self) -> None:
        image_info = {
            "image_info_list": [
                {"image_sort": 1, "image_type": 1, "image_url": "https://img.example.com/1.jpg"}
            ]
        }
        parent = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            active=True,
            sku="CONF-COLOR-SIZE",
        )
        rule, shein_product_type = self._create_product_type_rule(
            parent,
            remote_id="TYPE-3",
            category_id="CAT-3",
        )
        color_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        size_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        red = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=color_property)
        blue = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=color_property)
        small = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=size_property)
        large = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=size_property)

        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=rule,
            property=color_property,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            sort_order=0,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=rule,
            property=size_property,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            sort_order=1,
        )

        shein_color, _ = self._link_shein_property(
            property_obj=color_property,
            shein_product_type=shein_product_type,
            remote_id="COLOR",
            is_main=True,
        )
        shein_size, _ = self._link_shein_property(
            property_obj=size_property,
            shein_product_type=shein_product_type,
            remote_id="SIZE",
            is_main=False,
        )
        self._link_shein_value(shein_property=shein_color, local_value=red, remote_value="RED-2")
        self._link_shein_value(shein_property=shein_color, local_value=blue, remote_value="BLUE-2")
        self._link_shein_value(shein_property=shein_size, local_value=small, remote_value="SMALL-2")
        self._link_shein_value(shein_property=shein_size, local_value=large, remote_value="LARGE-2")

        red_small = self._create_variation(
            parent=parent,
            sku="CONF-RED-S",
            color_property=color_property,
            color_value=red,
            size_property=size_property,
            size_value=small,
        )
        blue_large = self._create_variation(
            parent=parent,
            sku="CONF-BLUE-L",
            color_property=color_property,
            color_value=blue,
            size_property=size_property,
            size_value=large,
        )
        self._assign_supplier_code(product=red_small, value="SUP-RED-2")
        self._assign_supplier_code(product=blue_large, value="SUP-BLUE-2")

        remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_sku=parent.sku,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=parent,
            sales_channel_view=self.view,
            remote_product=remote_product,
        )

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_instance=remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.remote_rule = type("Rule", (), {"category_id": shein_product_type.category_id, "remote_id": shein_product_type.remote_id})()
        factory.selected_category_id = shein_product_type.category_id
        factory.selected_product_type_id = shein_product_type.remote_id
        factory.rule = rule

        with (
            patch.object(
                SheinProductCreateFactory,
                "_build_media",
                autospec=True,
                side_effect=lambda self: setattr(self, "image_info", image_info),
            ),
            patch.object(
                SheinProductCreateFactory,
                "_build_image_info_for_product",
                autospec=True,
                return_value=image_info,
            ),
        ):
            payload = factory.build_payload()

        skc_list = sorted(payload["skc_list"], key=lambda skc: skc["sale_attribute"]["attribute_value_id"])
        payload["skc_list"] = skc_list
        expected_skc = [
            {
                "shelf_way": "1",
                "image_info": image_info,
                "sale_attribute": {"attribute_id": "COLOR", "attribute_value_id": "BLUE-2"},
                "supplier_code": "SUP-BLUE-2",
                "sku_list": [
                    {
                        "mall_state": 1,
                        "supplier_sku": blue_large.sku,
                        "supplier_code": "SUP-BLUE-2",
                        "stop_purchase": 1,
                        "height": "10.0",
                        "length": "10.0",
                        "width": "10.0",
                        "weight": 10,
                        "sale_attribute_list": [
                            {"attribute_id": "SIZE", "attribute_value_id": "LARGE-2"}
                        ],
                        "stock_info_list": [{"inventory_num": 5}],
                    }
                ],
            },
            {
                "shelf_way": "1",
                "image_info": image_info,
                "sale_attribute": {"attribute_id": "COLOR", "attribute_value_id": "RED-2"},
                "supplier_code": "SUP-RED-2",
                "sku_list": [
                    {
                        "mall_state": 1,
                        "supplier_sku": red_small.sku,
                        "supplier_code": "SUP-RED-2",
                        "stop_purchase": 1,
                        "height": "10.0",
                        "length": "10.0",
                        "width": "10.0",
                        "weight": 10,
                        "sale_attribute_list": [
                            {"attribute_id": "SIZE", "attribute_value_id": "SMALL-2"}
                        ],
                        "stock_info_list": [{"inventory_num": 5}],
                    }
                ],
            },
        ]

        expected = {
            "category_id": "CAT-3",
            "product_type_id": "TYPE-3",
            "source_system": "openapi",
            "site_list": [{"main_site": "shein", "sub_site_list": ["shein-fr"]}],
            "skc_list": expected_skc,
        }

        self.assertEqual(payload, expected, self._format_payload_debug(payload, expected))

    def test_shein_configurable_payload_with_three_configurator_attributes(self) -> None:
        image_info = {
            "image_info_list": [
                {"image_sort": 1, "image_type": 1, "image_url": "https://img.example.com/1.jpg"}
            ]
        }
        parent = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            active=True,
            sku="CONF-THREE-ATTR",
        )
        rule, shein_product_type = self._create_product_type_rule(
            parent,
            remote_id="TYPE-5",
            category_id="CAT-5",
        )
        color_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        size_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        material_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        red = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=color_property)
        blue = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=color_property)
        small = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=size_property)
        large = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=size_property)
        cotton = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=material_property)
        poly = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=material_property)

        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=rule,
            property=color_property,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            sort_order=0,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=rule,
            property=size_property,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            sort_order=1,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=rule,
            property=material_property,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            sort_order=2,
        )

        shein_color, _ = self._link_shein_property(
            property_obj=color_property,
            shein_product_type=shein_product_type,
            remote_id="COLOR",
            is_main=True,
        )
        shein_size, _ = self._link_shein_property(
            property_obj=size_property,
            shein_product_type=shein_product_type,
            remote_id="SIZE",
            is_main=False,
        )
        shein_material, _ = self._link_shein_property(
            property_obj=material_property,
            shein_product_type=shein_product_type,
            remote_id="MATERIAL",
            is_main=False,
        )
        self._link_shein_value(shein_property=shein_color, local_value=red, remote_value="RED-3")
        self._link_shein_value(shein_property=shein_color, local_value=blue, remote_value="BLUE-3")
        self._link_shein_value(shein_property=shein_size, local_value=small, remote_value="SMALL-3")
        self._link_shein_value(shein_property=shein_size, local_value=large, remote_value="LARGE-3")
        self._link_shein_value(shein_property=shein_material, local_value=cotton, remote_value="COT-3")
        self._link_shein_value(shein_property=shein_material, local_value=poly, remote_value="POLY-3")

        red_small = self._create_variation(
            parent=parent,
            sku="CONF-RED-S-COT",
            color_property=color_property,
            color_value=red,
            size_property=size_property,
            size_value=small,
        )
        blue_large = self._create_variation(
            parent=parent,
            sku="CONF-BLUE-L-POLY",
            color_property=color_property,
            color_value=blue,
            size_property=size_property,
            size_value=large,
        )
        self._assign_supplier_code(product=red_small, value="SUP-RED-3")
        self._assign_supplier_code(product=blue_large, value="SUP-BLUE-3")
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=red_small,
            property=material_property,
            value_select=cotton,
        )
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=blue_large,
            property=material_property,
            value_select=poly,
        )

        remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_sku=parent.sku,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=parent,
            sales_channel_view=self.view,
            remote_product=remote_product,
        )

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_instance=remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.remote_rule = type("Rule", (), {"category_id": shein_product_type.category_id, "remote_id": shein_product_type.remote_id})()
        factory.selected_category_id = shein_product_type.category_id
        factory.selected_product_type_id = shein_product_type.remote_id
        factory.rule = rule

        with (
            patch.object(
                SheinProductCreateFactory,
                "_build_media",
                autospec=True,
                side_effect=lambda self: setattr(self, "image_info", image_info),
            ),
            patch.object(
                SheinProductCreateFactory,
                "_build_image_info_for_product",
                autospec=True,
                return_value=image_info,
            ),
        ):
            payload = factory.build_payload()

        skc_list = sorted(payload["skc_list"], key=lambda skc: skc["sale_attribute"]["attribute_value_id"])
        payload["skc_list"] = skc_list
        expected_skc = [
            {
                "shelf_way": "1",
                "image_info": image_info,
                "sale_attribute": {"attribute_id": "COLOR", "attribute_value_id": "BLUE-3"},
                "supplier_code": "SUP-BLUE-3",
                "sku_list": [
                    {
                        "mall_state": 1,
                        "supplier_sku": blue_large.sku,
                        "supplier_code": "SUP-BLUE-3",
                        "stop_purchase": 1,
                        "height": "10.0",
                        "length": "10.0",
                        "width": "10.0",
                        "weight": 10,
                        "sale_attribute_list": [
                            {"attribute_id": "SIZE", "attribute_value_id": "LARGE-3"},
                            {"attribute_id": "MATERIAL", "attribute_value_id": "POLY-3"},
                        ],
                        "stock_info_list": [{"inventory_num": 5}],
                    }
                ],
            },
            {
                "shelf_way": "1",
                "image_info": image_info,
                "sale_attribute": {"attribute_id": "COLOR", "attribute_value_id": "RED-3"},
                "supplier_code": "SUP-RED-3",
                "sku_list": [
                    {
                        "mall_state": 1,
                        "supplier_sku": red_small.sku,
                        "supplier_code": "SUP-RED-3",
                        "stop_purchase": 1,
                        "height": "10.0",
                        "length": "10.0",
                        "width": "10.0",
                        "weight": 10,
                        "sale_attribute_list": [
                            {"attribute_id": "SIZE", "attribute_value_id": "SMALL-3"},
                            {"attribute_id": "MATERIAL", "attribute_value_id": "COT-3"},
                        ],
                        "stock_info_list": [{"inventory_num": 5}],
                    }
                ],
            },
        ]

        expected = {
            "category_id": "CAT-5",
            "product_type_id": "TYPE-5",
            "source_system": "openapi",
            "site_list": [{"main_site": "shein", "sub_site_list": ["shein-fr"]}],
            "skc_list": expected_skc,
        }

        self.assertEqual(payload, expected, self._format_payload_debug(payload, expected))

    def test_shein_configurable_payload_with_four_configurator_attributes_raises(self) -> None:
        parent = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            active=True,
            sku="CONF-THREE",
        )
        prop_a = baker.make(Property, multi_tenant_company=self.multi_tenant_company, type=Property.TYPES.SELECT)
        prop_b = baker.make(Property, multi_tenant_company=self.multi_tenant_company, type=Property.TYPES.SELECT)
        prop_c = baker.make(Property, multi_tenant_company=self.multi_tenant_company, type=Property.TYPES.SELECT)
        prop_d = baker.make(Property, multi_tenant_company=self.multi_tenant_company, type=Property.TYPES.SELECT)
        val_a1 = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=prop_a)
        val_a2 = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=prop_a)
        val_b1 = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=prop_b)
        val_b2 = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=prop_b)
        val_c1 = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=prop_c)
        val_c2 = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=prop_c)
        val_d1 = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=prop_d)
        val_d2 = baker.make(PropertySelectValue, multi_tenant_company=self.multi_tenant_company, property=prop_d)

        variation_one = self._create_variation(
            parent=parent,
            sku="CONF-A1",
            color_property=prop_a,
            color_value=val_a1,
            size_property=prop_b,
            size_value=val_b1,
        )
        variation_two = self._create_variation(
            parent=parent,
            sku="CONF-A2",
            color_property=prop_a,
            color_value=val_a2,
            size_property=prop_b,
            size_value=val_b2,
        )
        for variation, val in ((variation_one, val_c1), (variation_two, val_c2)):
            ProductProperty.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=variation,
                property=prop_c,
                value_select=val,
            )
        for variation, val in ((variation_one, val_d1), (variation_two, val_d2)):
            ProductProperty.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=variation,
                property=prop_d,
                value_select=val,
            )

        remote_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_sku=parent.sku,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=parent,
            sales_channel_view=self.view,
            remote_product=remote_product,
        )

        factory = SheinProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=parent,
            remote_instance=remote_product,
            get_value_only=True,
            skip_checks=True,
        )
        factory.remote_rule = type("Rule", (), {"category_id": "CAT-4", "remote_id": "TYPE-4"})()

        configurator_items = [
            SimpleNamespace(property_id=prop_a.id, sort_order=0),
            SimpleNamespace(property_id=prop_b.id, sort_order=1),
            SimpleNamespace(property_id=prop_c.id, sort_order=2),
            SimpleNamespace(property_id=prop_d.id, sort_order=3),
        ]

        def fake_get_configurator_items(self):
            return configurator_items

        with (
            patch.object(SheinProductCreateFactory, "_build_property_payloads"),
            patch.object(SheinProductCreateFactory, "_build_prices"),
            patch.object(SheinProductCreateFactory, "_build_media"),
            patch.object(SheinProductCreateFactory, "_build_translations"),
            patch.object(SheinProductCreateFactory, "_get_configurator_rule_items", autospec=True, side_effect=lambda self: fake_get_configurator_items(self)),
        ):
            with self.assertRaises(SheinConfiguratorAttributesLimitError):
                factory.build_payload()
