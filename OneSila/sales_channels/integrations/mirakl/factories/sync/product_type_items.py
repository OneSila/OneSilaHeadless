from __future__ import annotations

from sales_channels.integrations.mirakl.models import MiraklProductType, MiraklProductTypeItem


class MiraklProductTypeItemCloneFactory:
    """Clone product type items from an imported Mirakl type sharing the same remote id."""

    def __init__(self, *, product_type: MiraklProductType) -> None:
        self.product_type = product_type

    def run(self) -> int:
        remote_id = str(self.product_type.remote_id or "").strip()
        if not remote_id or not self.product_type.local_instance_id:
            return 0

        source = self._get_source_product_type(remote_id=remote_id)
        if source is None:
            return 0

        self._copy_product_type_metadata(source=source)
        return self._clone_items(source=source)

    def _get_source_product_type(self, *, remote_id: str) -> MiraklProductType | None:
        queryset = (
            MiraklProductType.objects.filter(
                sales_channel=self.product_type.sales_channel,
                remote_id=remote_id,
            )
            .exclude(pk=self.product_type.pk)
            .filter(items__isnull=False)
            .select_related("category")
            .distinct()
        )

        source = queryset.filter(imported=True, local_instance__isnull=True).order_by("id").first()
        if source is not None:
            return source

        return queryset.order_by("id").first()

    def _copy_product_type_metadata(self, *, source: MiraklProductType) -> None:
        updates = []
        if source.category_id and self.product_type.category_id != source.category_id:
            self.product_type.category = source.category
            updates.append("category")
        if source.name and self.product_type.name != source.name:
            self.product_type.name = source.name
            updates.append("name")

        if updates:
            self.product_type.save(update_fields=updates)

    def _clone_items(self, *, source: MiraklProductType) -> int:
        cloned = 0
        target_rule_items_by_property = self._get_target_rule_items_by_property()

        source_items = (
            MiraklProductTypeItem.objects.filter(product_type=source)
            .select_related("remote_property", "local_instance")
            .order_by("id")
        )
        for source_item in source_items:
            local_rule_item = None
            local_property_id = getattr(source_item.remote_property, "local_instance_id", None)
            if local_property_id:
                local_rule_item = target_rule_items_by_property.get(local_property_id)

            target_item, created = MiraklProductTypeItem.objects.get_or_create(
                multi_tenant_company=self.product_type.multi_tenant_company,
                product_type=self.product_type,
                remote_property=source_item.remote_property,
                sales_channel=self.product_type.sales_channel,
            )
            target_item.sales_channel = self.product_type.sales_channel
            target_item.multi_tenant_company = self.product_type.multi_tenant_company
            target_item.local_instance = local_rule_item
            target_item.remote_id = source_item.remote_id
            target_item.hierarchy_code = source_item.hierarchy_code
            target_item.required = source_item.required
            target_item.variant = source_item.variant
            target_item.requirement_level = source_item.requirement_level
            target_item.value_list_code = source_item.value_list_code
            target_item.value_list_label = source_item.value_list_label
            target_item.role_data = source_item.role_data
            target_item.raw_data = source_item.raw_data
            target_item.save()
            if created:
                cloned += 1

        return cloned

    def _get_target_rule_items_by_property(self) -> dict[int, object]:
        rule = self.product_type.local_instance
        if rule is None:
            return {}

        return {
            item.property_id: item
            for item in rule.items.select_related("property").all()
        }
