from core.tests import TestCase
from model_bakery import baker

from properties.models import Property, PropertySelectValue
from sales_channels.integrations.mirakl.factories.sync import (
    MiraklPropertySelectValueSiblingMappingFactory,
)
from sales_channels.integrations.mirakl.models import (
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklSalesChannel,
)


class MiraklPropertySelectValueSiblingMappingFactoryTests(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
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

    def _make_remote_property(self, *, code: str, local_property: Property | None = None, sales_channel=None) -> MiraklProperty:
        return baker.make(
            MiraklProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel or self.sales_channel,
            code=code,
            type=Property.TYPES.SELECT,
            local_instance=local_property or self.local_property,
        )

    def _make_remote_value(
        self,
        *,
        remote_property: MiraklProperty,
        code: str,
        value: str,
        local_instance: PropertySelectValue | None = None,
    ) -> MiraklPropertySelectValue:
        return baker.make(
            MiraklPropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=remote_property.sales_channel,
            remote_property=remote_property,
            code=code,
            value=value,
            local_instance=local_instance,
        )

    def test_maps_unmapped_sibling_with_same_code(self):
        current_property = self._make_remote_property(code="color")
        sibling_property = self._make_remote_property(code="colourgroup")
        current_value = self._make_remote_value(
            remote_property=current_property,
            code="purple",
            value="Purple",
            local_instance=self.local_value,
        )
        sibling_value = self._make_remote_value(
            remote_property=sibling_property,
            code="purple",
            value="Purple Group",
        )

        MiraklPropertySelectValueSiblingMappingFactory(
            remote_select_value=current_value,
        ).run()

        sibling_value.refresh_from_db()
        self.assertEqual(sibling_value.local_instance, self.local_value)

    def test_maps_unmapped_sibling_with_same_value(self):
        current_property = self._make_remote_property(code="color")
        sibling_property = self._make_remote_property(code="colourgroup")
        current_value = self._make_remote_value(
            remote_property=current_property,
            code="purple_primary",
            value="Purple",
            local_instance=self.local_value,
        )
        sibling_value = self._make_remote_value(
            remote_property=sibling_property,
            code="group_a",
            value="Purple",
        )

        MiraklPropertySelectValueSiblingMappingFactory(
            remote_select_value=current_value,
        ).run()

        sibling_value.refresh_from_db()
        self.assertEqual(sibling_value.local_instance, self.local_value)

    def test_does_not_map_across_different_local_property_or_channel(self):
        other_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl-second.example.com",
            shop_id=456,
            api_key="secret-token-2",
        )
        other_local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        current_property = self._make_remote_property(code="color")
        sibling_other_property = self._make_remote_property(
            code="colourgroup",
            local_property=other_local_property,
        )
        sibling_other_channel_property = self._make_remote_property(
            code="colourgroup_other_channel",
            sales_channel=other_channel,
        )
        current_value = self._make_remote_value(
            remote_property=current_property,
            code="purple",
            value="Purple",
            local_instance=self.local_value,
        )
        different_property_value = self._make_remote_value(
            remote_property=sibling_other_property,
            code="purple",
            value="Purple",
        )
        different_channel_value = self._make_remote_value(
            remote_property=sibling_other_channel_property,
            code="purple",
            value="Purple",
        )

        MiraklPropertySelectValueSiblingMappingFactory(
            remote_select_value=current_value,
        ).run()

        different_property_value.refresh_from_db()
        different_channel_value.refresh_from_db()
        self.assertIsNone(different_property_value.local_instance)
        self.assertIsNone(different_channel_value.local_instance)

    def test_leaves_existing_mapping_and_does_not_cross_match_code_to_value(self):
        other_local_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=self.local_property,
        )
        current_property = self._make_remote_property(code="capacity")
        sibling_property = self._make_remote_property(code="capacity_group")
        current_value = self._make_remote_value(
            remote_property=current_property,
            code="15_litre",
            value="15 Litre",
            local_instance=self.local_value,
        )
        mapped_sibling_value = self._make_remote_value(
            remote_property=sibling_property,
            code="15_litre",
            value="15 Litre",
            local_instance=other_local_value,
        )
        cross_match_sibling_value = self._make_remote_value(
            remote_property=sibling_property,
            code="15 Litre",
            value="Capacity Group",
        )

        MiraklPropertySelectValueSiblingMappingFactory(
            remote_select_value=current_value,
        ).run()

        mapped_sibling_value.refresh_from_db()
        cross_match_sibling_value.refresh_from_db()
        self.assertEqual(mapped_sibling_value.local_instance, other_local_value)
        self.assertIsNone(cross_match_sibling_value.local_instance)
