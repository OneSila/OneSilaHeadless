from sales_channels.factories.task_queue import (
    ChannelScopedAddTask,
    DeleteScopedAddTask,
    GuardResult,
    ProductContentAddTask,
    ProductDocumentsAddTask,
    ProductEanCodeAddTask,
    ProductImagesAddTask,
    ProductPriceAddTask,
    ProductPropertyAddTask,
    ProductUpdateAddTask,
    SingleChannelAddTask,
    SingleViewAddTask,
    ViewScopedAddTask,
)
from sales_channels.integrations.mirakl.models import (
    MiraklProduct,
    MiraklProductCategory,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklSalesChannel,
)
from sales_channels.integrations.mirakl.tasks import resync_mirakl_product_db_task
from sales_channels.models import SalesChannelViewAssign


class MiraklChannelAddTask(ChannelScopedAddTask):
    sales_channel_class = MiraklSalesChannel


class MiraklSingleChannelAddTask(SingleChannelAddTask, MiraklChannelAddTask):
    pass


class MiraklSingleViewAddTask(SingleViewAddTask, MiraklChannelAddTask):
    pass


class MiraklMarketplaceViewAddTask(ViewScopedAddTask, MiraklChannelAddTask):
    view_assign_model = SalesChannelViewAssign

    def build_task_kwargs(self, *, target):
        task_kwargs = super().build_task_kwargs(target=target)
        view_id = getattr(target.sales_channel_view, "id", target.sales_channel_view)
        if view_id:
            task_kwargs["sales_channel_view_id"] = view_id
            task_kwargs["view_id"] = view_id
        return task_kwargs


class MiraklDeleteScopedAddTask(DeleteScopedAddTask, MiraklChannelAddTask):
    pass


class MiraklNonLiveMarketplaceViewAddTask(MiraklMarketplaceViewAddTask):
    live = False
    product_task_fallback = resync_mirakl_product_db_task


class MiraklProductContentAddTask(ProductContentAddTask, MiraklNonLiveMarketplaceViewAddTask):
    pass


class MiraklProductPriceAddTask(ProductPriceAddTask, MiraklNonLiveMarketplaceViewAddTask):
    pass


class MiraklProductImagesAddTask(ProductImagesAddTask, MiraklNonLiveMarketplaceViewAddTask):
    pass


class MiraklProductDocumentsAddTask(ProductDocumentsAddTask, MiraklNonLiveMarketplaceViewAddTask):
    pass


class MiraklProductPropertyAddTask(ProductPropertyAddTask, MiraklNonLiveMarketplaceViewAddTask):
    def _get_product_type(self, *, sales_channel):
        category_remote_id = (
            MiraklProductCategory.objects.filter(
                product=self.product,
                sales_channel=sales_channel,
            )
            .exclude(remote_id__in=(None, ""))
            .values_list("remote_id", flat=True)
            .first()
        )
        if category_remote_id:
            product_type = (
                MiraklProductType.objects.filter(
                    sales_channel=sales_channel,
                    category__remote_id=category_remote_id,
                )
                .select_related("category", "local_instance")
                .first()
            )
            if product_type is not None:
                return product_type

        if getattr(self, "rule", None) is None:
            return None

        return (
            MiraklProductType.objects.filter(
                sales_channel=sales_channel,
                local_instance=self.rule,
            )
            .select_related("category", "local_instance")
            .first()
        )

    def guard(self, *, target):
        guard_result = super().guard(target=target)
        if not guard_result.allowed:
            return guard_result

        product_property = self.local_instance
        property_obj = getattr(product_property, "property", None) if product_property else None
        if property_obj is None:
            return GuardResult(allowed=False, reason="mirakl_property_missing")

        mirakl_properties = MiraklProperty.objects.filter(
            local_instance=property_obj,
            sales_channel=target.sales_channel,
        )
        if not mirakl_properties.exists():
            return GuardResult(allowed=False, reason="mirakl_property_not_mapped")

        product_type = self._get_product_type(sales_channel=target.sales_channel)
        if product_type is None:
            return GuardResult(allowed=False, reason="mirakl_product_type_missing")

        if not MiraklProductTypeItem.objects.filter(
            product_type=product_type,
            remote_property__in=mirakl_properties,
        ).exists():
            return GuardResult(allowed=False, reason="mirakl_property_not_in_type")

        if property_obj.type in {property_obj.TYPES.SELECT, property_obj.TYPES.MULTISELECT}:
            mirakl_properties_without_custom_values = mirakl_properties.filter(allows_unmapped_values=False)
            if not mirakl_properties_without_custom_values.exists():
                return guard_result

            if property_obj.type == property_obj.TYPES.SELECT:
                select_value = getattr(product_property, "value_select", None)
                if select_value is None:
                    return GuardResult(allowed=False, reason="mirakl_select_value_missing")
                is_mapped = MiraklPropertySelectValue.objects.filter(
                    remote_property__in=mirakl_properties_without_custom_values,
                    local_instance=select_value,
                ).exists()
                if not is_mapped:
                    return GuardResult(allowed=False, reason="mirakl_select_value_unmapped")

            if property_obj.type == property_obj.TYPES.MULTISELECT:
                values = list(product_property.value_multi_select.all())
                if not values:
                    return GuardResult(allowed=False, reason="mirakl_multiselect_value_missing")
                mapped_ids = set(
                    MiraklPropertySelectValue.objects.filter(
                        remote_property__in=mirakl_properties_without_custom_values,
                        local_instance__in=values,
                    ).values_list("local_instance_id", flat=True)
                )
                if any(value.id not in mapped_ids for value in values):
                    return GuardResult(allowed=False, reason="mirakl_multiselect_value_unmapped")

        return guard_result


class MiraklProductUpdateAddTask(ProductUpdateAddTask, MiraklNonLiveMarketplaceViewAddTask):
    pass


class MiraklProductEanCodeAddTask(ProductEanCodeAddTask, MiraklNonLiveMarketplaceViewAddTask):
    pass


class MiraklProductDeleteAddTask(MiraklDeleteScopedAddTask):
    remote_class = MiraklProduct
