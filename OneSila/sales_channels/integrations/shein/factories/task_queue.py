from sales_channels.factories.task_queue import (
    ChannelScopedAddTask,
    GuardResult,
    ProductContentAddTask,
    ProductEanCodeAddTask,
    ProductImagesAddTask,
    ProductPriceAddTask,
    ProductPropertyAddTask,
    ProductUpdateAddTask,
    SingleChannelAddTask,
)
from sales_channels.integrations.shein.models import (
    SheinProductCategory,
    SheinProductType,
    SheinProductTypeItem,
    SheinProperty,
    SheinPropertySelectValue,
    SheinSalesChannel,
)
from sales_channels.integrations.shein.tasks import resync_shein_product_db_task


class SheinChannelAddTask(ChannelScopedAddTask):
    sales_channel_class = SheinSalesChannel


class SheinSingleChannelAddTask(SingleChannelAddTask, SheinChannelAddTask):
    pass


class SheinNonLiveChannelAddTask(SheinChannelAddTask):
    live = False
    product_task_fallback = resync_shein_product_db_task


class SheinProductContentAddTask(ProductContentAddTask, SheinNonLiveChannelAddTask):
    pass


class SheinProductPriceAddTask(ProductPriceAddTask, SheinNonLiveChannelAddTask):
    pass


class SheinProductImagesAddTask(ProductImagesAddTask, SheinNonLiveChannelAddTask):
    pass


class SheinProductPropertyAddTask(ProductPropertyAddTask, SheinNonLiveChannelAddTask):
    def _get_category_id(self, sales_channel) -> str | None:
        product = getattr(self, "product", None)
        if product is None:
            return None

        category = (
            SheinProductCategory.objects.filter(
                product=product,
                sales_channel=sales_channel,
            )
            .exclude(product_type_remote_id__in=(None, ""))
            .values_list("product_type_remote_id", flat=True)
            .first()
        )
        if category:
            candidate = str(category).strip()
            if candidate:
                return candidate

        product_type_remote_id = (
            SheinProductType.objects.filter(
                sales_channel=sales_channel,
                local_instance=self.rule,
            )
            .exclude(remote_id__in=(None, ""))
            .values_list("remote_id", flat=True)
            .first()
        )
        if product_type_remote_id:
            candidate = str(product_type_remote_id).strip()
            if candidate:
                return candidate

        return None

    def guard(self, *, target):
        guard_result = super().guard(target=target)
        if not guard_result.allowed:
            return guard_result

        product_property = self.local_instance
        property_obj = getattr(product_property, "property", None) if product_property else None
        if property_obj is None:
            return GuardResult(allowed=False, reason="shein_property_missing")

        shein_properties = SheinProperty.objects.filter(
            local_instance=property_obj,
            sales_channel=target.sales_channel,
        )
        if not shein_properties.exists():
            return GuardResult(allowed=False, reason="shein_property_not_mapped")

        category_id = self._get_category_id(target.sales_channel)
        if not category_id:
            return GuardResult(allowed=False, reason="shein_category_missing")

        if not SheinProductTypeItem.objects.filter(
            property__in=shein_properties,
            product_type__remote_id=category_id,
            product_type__sales_channel=target.sales_channel,
        ).exists():
            return GuardResult(allowed=False, reason="shein_attribute_not_allowed_in_category")

        if property_obj.type in {property_obj.TYPES.SELECT, property_obj.TYPES.MULTISELECT}:
            allow_custom = shein_properties.filter(
                value_mode=SheinProperty.ValueModes.MULTI_SELECT_WITH_CUSTOM
            ).exists()
            if allow_custom:
                return guard_result

            if property_obj.type == property_obj.TYPES.SELECT:
                select_value = getattr(product_property, "value_select", None)
                if select_value is None:
                    return GuardResult(allowed=False, reason="shein_select_value_missing")
                is_mapped = SheinPropertySelectValue.objects.filter(
                    remote_property__in=shein_properties,
                    local_instance=select_value,
                ).exists()
                if not is_mapped:
                    return GuardResult(allowed=False, reason="shein_select_value_unmapped")

            if property_obj.type == property_obj.TYPES.MULTISELECT:
                values = list(product_property.value_multi_select.all())
                if not values:
                    return GuardResult(allowed=False, reason="shein_multiselect_value_missing")
                mapped_ids = set(
                    SheinPropertySelectValue.objects.filter(
                        remote_property__in=shein_properties,
                        local_instance__in=values,
                    ).values_list("local_instance_id", flat=True)
                )
                if any(value.id not in mapped_ids for value in values):
                    return GuardResult(allowed=False, reason="shein_multiselect_value_unmapped")

        return guard_result


class SheinProductUpdateAddTask(ProductUpdateAddTask, SheinNonLiveChannelAddTask):
    pass


class SheinProductEanCodeAddTask(ProductEanCodeAddTask, SheinNonLiveChannelAddTask):
    pass
