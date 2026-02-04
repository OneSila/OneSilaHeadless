from sales_channels.factories.task_queue import (
    ChannelScopedAddTask,
    GuardResult,
    ProductContentAddTask,
    ProductEanCodeAddTask,
    ProductImagesAddTask,
    ProductPriceAddTask,
    ProductPropertyAddTask,
    ProductUpdateAddTask,
    SingleViewAddTask,
    ViewScopedAddTask,
)
from sales_channels.integrations.amazon.models import (
    AmazonProductType,
    AmazonProductTypeItem,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonSalesChannel,
)
from sales_channels.integrations.amazon.tasks import resync_amazon_product_db_task
from sales_channels.models import SalesChannelViewAssign


class AmazonChannelAddTask(ChannelScopedAddTask):
    sales_channel_class = AmazonSalesChannel


class AmazonMarketplaceViewAddTask(ViewScopedAddTask, AmazonChannelAddTask):
    view_assign_model = SalesChannelViewAssign

    def build_task_kwargs(self, *, target):
        task_kwargs = super().build_task_kwargs(target=target)
        view_id = getattr(target.sales_channel_view, "id", target.sales_channel_view)
        if view_id:
            task_kwargs["sales_channel_view_id"] = view_id
            task_kwargs["view_id"] = view_id
        return task_kwargs


class AmazonNonLiveMarketplaceViewAddTask(AmazonMarketplaceViewAddTask):
    live = False
    product_task_fallback = resync_amazon_product_db_task


class AmazonSingleViewAddTask(SingleViewAddTask, AmazonChannelAddTask):
    pass


class AmazonProductContentAddTask(ProductContentAddTask, AmazonNonLiveMarketplaceViewAddTask):
    pass


class AmazonProductPriceAddTask(ProductPriceAddTask, AmazonNonLiveMarketplaceViewAddTask):
    pass


class AmazonProductImagesAddTask(ProductImagesAddTask, AmazonNonLiveMarketplaceViewAddTask):
    pass


class AmazonProductPropertyAddTask(ProductPropertyAddTask, AmazonNonLiveMarketplaceViewAddTask):
    def guard(self, *, target):
        guard_result = super().guard(target=target)
        if not guard_result.allowed:
            return guard_result

        if target.sales_channel_view is None:
            return GuardResult(allowed=False, reason="amazon_view_missing")

        product_property = self.local_instance
        property_obj = getattr(product_property, "property", None) if product_property else None
        if property_obj is None:
            return GuardResult(allowed=False, reason="amazon_property_missing")

        amazon_properties = AmazonProperty.objects.filter(
            local_instance=property_obj,
            sales_channel=target.sales_channel,
        )
        if not amazon_properties.exists():
            return GuardResult(allowed=False, reason="amazon_property_not_mapped")

        amazon_rule = AmazonProductType.objects.filter(
            local_instance=self.rule,
            sales_channel=target.sales_channel,
        ).first()
        if not amazon_rule:
            return GuardResult(allowed=False, reason="amazon_product_type_missing")

        if not AmazonProductTypeItem.objects.filter(
            amazon_rule=amazon_rule,
            remote_property__in=amazon_properties,
        ).exists():
            return GuardResult(allowed=False, reason="amazon_property_not_in_type")

        if property_obj.type in {property_obj.TYPES.SELECT, property_obj.TYPES.MULTISELECT}:
            amazon_properties_without_custom_values = amazon_properties.filter(allows_unmapped_values=False)
            if not amazon_properties_without_custom_values.exists():
                return guard_result

            if property_obj.type == property_obj.TYPES.SELECT:
                select_value = getattr(product_property, "value_select", None)
                if select_value is None:
                    return GuardResult(allowed=False, reason="amazon_select_value_missing")
                is_mapped = AmazonPropertySelectValue.objects.filter(
                    amazon_property__in=amazon_properties_without_custom_values,
                    marketplace=target.sales_channel_view,
                    local_instance=select_value,
                ).exists()
                if not is_mapped:
                    return GuardResult(allowed=False, reason="amazon_select_value_unmapped")

            if property_obj.type == property_obj.TYPES.MULTISELECT:
                values = list(product_property.value_multi_select.all())
                if not values:
                    return GuardResult(allowed=False, reason="amazon_multiselect_value_missing")
                mapped_ids = set(
                    AmazonPropertySelectValue.objects.filter(
                        amazon_property__in=amazon_properties_without_custom_values,
                        marketplace=target.sales_channel_view,
                        local_instance__in=values,
                    ).values_list("local_instance_id", flat=True)
                )
                if any(value.id not in mapped_ids for value in values):
                    return GuardResult(allowed=False, reason="amazon_multiselect_value_unmapped")

        return guard_result


class AmazonProductUpdateAddTask(ProductUpdateAddTask, AmazonNonLiveMarketplaceViewAddTask):
    pass


class AmazonProductEanCodeAddTask(ProductEanCodeAddTask, AmazonNonLiveMarketplaceViewAddTask):
    pass
