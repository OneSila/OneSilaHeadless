"""Tests for eBay sync factories and tasks."""

from __future__ import annotations

from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker
from properties.models import (
    ProductPropertiesRule,
    ProductPropertiesRuleItem,
    Property,
    PropertySelectValue,
    PropertySelectValueTranslation,
    PropertyTranslation,
)
from sales_channels.integrations.ebay.factories.sync import (
    EbayPropertyRuleItemSyncFactory,
)
from sales_channels.integrations.ebay.models import (
    EbayProductType,
    EbayProductTypeItem,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannel,
    EbaySalesChannelView,
    EbayRemoteLanguage,
)
from sales_channels.integrations.ebay.tasks import (
    ebay_translate_property_task,
    ebay_translate_select_value_task,
)


class EbaySyncFactoriesTest(TestCase):
    """Validate eBay specific sync helpers."""

    def setUp(self) -> None:
        super().setUp()
        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.save(update_fields=["language"])

        self.sales_channel = EbaySalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="test.ebay",
            environment=EbaySalesChannel.PRODUCTION,
        )
        self.view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="EBAY_GB",
            name="UK",
            is_default=True,
        )

        EbayRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_code="de",
            local_instance="de",
        )

        self.product_type_property = (
            Property.objects.filter(
                is_product_type=True,
                multi_tenant_company=self.multi_tenant_company,
            ).first()
        )
        if not self.product_type_property:
            self.product_type_property = Property.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                type=Property.TYPES.SELECT,
                is_product_type=True,
                internal_name="product_type",
            )
            PropertyTranslation.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                property=self.product_type_property,
                language=self.multi_tenant_company.language,
                name="Product Type",
            )

        self.product_type_value = (
            PropertySelectValue.objects.filter(
                property=self.product_type_property,
                multi_tenant_company=self.multi_tenant_company,
            ).first()
        )
        if not self.product_type_value:
            self.product_type_value = PropertySelectValue.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                property=self.product_type_property,
            )
            PropertySelectValueTranslation.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                propertyselectvalue=self.product_type_value,
                language=self.multi_tenant_company.language,
                value="Default",
            )

        self.rule, _ = ProductPropertiesRule.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type_value,
        )

        self.local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
            is_product_type=False,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.local_property,
            language=self.multi_tenant_company.language,
            name="Color",
        )

    def _create_remote_property(self, *, localized_name: str = "Farbe") -> EbayProperty:
        return EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            localized_name=localized_name,
            local_instance=self.local_property,
        )

    def test_property_rule_item_sync_creates_rule_item(self) -> None:
        remote_property = self._create_remote_property()
        product_type = EbayProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="123",
            local_instance=self.rule,
        )
        EbayProductTypeItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type=product_type,
            ebay_property=remote_property,
            remote_type=ProductPropertiesRuleItem.REQUIRED,
        )

        EbayPropertyRuleItemSyncFactory(remote_property).run()

        rule_item = ProductPropertiesRuleItem.objects.get(
            rule=self.rule,
            property=self.local_property,
        )
        self.assertEqual(rule_item.type, ProductPropertiesRuleItem.REQUIRED)

    @patch("llm.flows.remote_translations.RemotePropertyTranslationLLM")
    def test_translate_property_task_translates_when_languages_differ(self, mock_translator) -> None:
        mock_translator.return_value.translate.return_value = "Color"
        remote_property = self._create_remote_property()

        ebay_translate_property_task.call_local(remote_property.id)

        mock_translator.assert_called_once()
        remote_property.refresh_from_db()
        self.assertEqual(remote_property.translated_name, "Color")

    @patch("llm.flows.remote_translations.RemotePropertyTranslationLLM")
    def test_translate_property_task_copies_when_language_matches(self, mock_translator) -> None:
        remote_language = self.view.remote_languages.first()
        remote_language.local_instance = "en"
        remote_language.save(update_fields=["local_instance"])

        remote_property = self._create_remote_property(localized_name="Color")

        ebay_translate_property_task.call_local(remote_property.id)

        mock_translator.assert_not_called()
        remote_property.refresh_from_db()
        self.assertEqual(remote_property.translated_name, "Color")

    @patch("llm.flows.remote_translations.RemoteSelectValueTranslationLLM")
    def test_translate_select_value_task_translates(self, mock_translator) -> None:
        mock_translator.return_value.translate.return_value = "Black"
        remote_property = self._create_remote_property()
        select_value = EbayPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            ebay_property=remote_property,
            marketplace=self.view,
            localized_value="Schwarz",
        )

        ebay_translate_select_value_task.call_local(select_value.id)

        mock_translator.assert_called_once()
        select_value.refresh_from_db()
        self.assertEqual(select_value.translated_value, "Black")
