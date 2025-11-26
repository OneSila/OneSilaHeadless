"""Tests for the EbayProductTypeRemoteMappingFactory."""

from __future__ import annotations

from unittest.mock import PropertyMock, patch

from properties.models import (
    ProductPropertiesRule,
    Property,
    PropertySelectValue,
    PropertySelectValueTranslation,
)
from sales_channels.integrations.ebay.factories.sales_channels import (
    EbayProductTypeRemoteMappingFactory,
)
from sales_channels.integrations.ebay.models import EbayProductType, EbaySalesChannelView

from .mixins import TestCaseEbayMixin


class TestEbayProductTypeRemoteMappingFactory(TestCaseEbayMixin):
    """Validate mirroring of eBay product type mappings across marketplaces."""

    def setUp(self) -> None:
        super().setUp()
        self.product_type_property = Property.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True,
        ).first()
        if self.product_type_property is None:
            self.product_type_property = Property.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                type=Property.TYPES.SELECT,
                is_product_type=True,
            )
        self.product_type_value, _ = PropertySelectValue.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property,
        )
        PropertySelectValueTranslation.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.product_type_value,
            language=self.multi_tenant_company.language,
            defaults={"value": "1990s"},
        )
        self.rule, _ = ProductPropertiesRule.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type_value,
        )

        self.view_gb = EbaySalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="EBAY_GB",
            default_category_tree_id="3",
            is_default=True,
        )
        self.view_us = EbaySalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            remote_id="EBAY_US",
            default_category_tree_id="205",
            is_default=False,
        )

        self.ensure_ebay_leaf_category(
            remote_id="72548",
            view=self.view_gb,
            name="Collectibles",
        )
        self.ensure_ebay_leaf_category(
            remote_id="72548",
            view=self.view_us,
            name="Collectibles US",
        )
        self.ensure_ebay_leaf_category(
            remote_id="99999",
            view=self.view_us,
            name="Existing Mapping",
        )

        self.product_type_gb = EbayProductType.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            marketplace=self.view_gb,
            local_instance=self.rule,
            imported=False,
        )
        self.product_type_us = EbayProductType.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            marketplace=self.view_us,
            local_instance=self.rule,
            imported=False,
        )

    def test_run_assigns_remote_id_to_matching_marketplaces(self) -> None:
        """Direct factory execution mirrors the remote id to sibling marketplaces."""

        self.product_type_gb.remote_id = "72548"
        factory = EbayProductTypeRemoteMappingFactory(product_type=self.product_type_gb)
        with patch.object(
            EbayProductType,
            "has_errors",
            new_callable=PropertyMock,
            return_value=False,
        ):
            with patch.object(
                EbayProductTypeRemoteMappingFactory,
                "_collect_target_tree_ids",
                return_value={"205"},
            ):
                factory.run()

        self.product_type_us.refresh_from_db()
        self.assertEqual(self.product_type_us.remote_id, "72548")

    def test_collect_target_tree_ids_uses_category_matches(self) -> None:
        """Category lookups exclude the source tree and normalise identifiers."""

        factory = EbayProductTypeRemoteMappingFactory(product_type=self.product_type_gb)
        with patch(
            "sales_channels.integrations.ebay.factories.sales_channels.product_type_mapping.EbayCategory.objects.filter",
        ) as mock_filter:
            mock_queryset = mock_filter.return_value
            mock_exclude = mock_queryset.exclude.return_value
            mock_exclude.values_list.return_value = ["205", None]

            result = factory._collect_target_tree_ids(remote_id="72548", source_tree_id="3")

        self.assertEqual(result, {"205"})
        mock_filter.assert_called_once_with(remote_id="72548")
        mock_queryset.exclude.assert_called_once_with(marketplace_default_tree_id="3")
        mock_exclude.values_list.assert_called_once_with("marketplace_default_tree_id", flat=True)

    def test_run_does_not_override_existing_remote_id(self) -> None:
        """Existing mappings on other marketplaces remain untouched."""

        EbayProductType.objects.filter(pk=self.product_type_us.pk).update(remote_id="99999")

        self.product_type_gb.remote_id = "72548"
        with patch.object(
            EbayProductType,
            "has_errors",
            new_callable=PropertyMock,
            return_value=False,
        ):
            with patch.object(
                EbayProductTypeRemoteMappingFactory,
                "_collect_target_tree_ids",
                return_value={"205"},
            ):
                EbayProductTypeRemoteMappingFactory(product_type=self.product_type_gb).run()

        self.product_type_us.refresh_from_db()
        self.assertEqual(self.product_type_us.remote_id, "99999")

    def test_signal_propagates_remote_id_on_update(self) -> None:
        """Saving a remote id triggers propagation through the registered receiver."""

        self.product_type_gb.remote_id = "72548"
        with patch.object(
            EbayProductType,
            "has_errors",
            new_callable=PropertyMock,
            return_value=False,
        ):
            with patch.object(
                EbayProductTypeRemoteMappingFactory,
                "_collect_target_tree_ids",
                return_value={"205"},
            ):
                self.product_type_gb.save(update_fields=["remote_id"])

        self.product_type_us.refresh_from_db()
        self.assertEqual(self.product_type_us.remote_id, "72548")
