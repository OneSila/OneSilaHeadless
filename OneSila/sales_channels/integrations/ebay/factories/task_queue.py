from sales_channels.factories.task_queue import (
    ChannelScopedAddTask,
    GuardResult,
    ProductContentAddTask,
    ProductDocumentsAddTask,
    ProductEanCodeAddTask,
    ProductImagesAddTask,
    ProductPriceAddTask,
    ProductPropertyAddTask,
    ProductUpdateAddTask,
    SingleViewAddTask,
    ViewScopedAddTask,
)
from sales_channels.integrations.ebay.models import (
    EbayProductCategory,
    EbayDocumentType,
    EbayProperty,
    EbayPropertySelectValue,
    EbayProductType,
    EbayProductTypeItem,
    EbaySalesChannel,
)
from sales_channels.integrations.ebay.tasks import resync_ebay_product_db_task
from sales_channels.models import SalesChannelViewAssign

class EbayChannelAddTask(ChannelScopedAddTask):
    sales_channel_class = EbaySalesChannel


class EbayMarketplaceViewAddTask(ViewScopedAddTask, EbayChannelAddTask):
    view_assign_model = SalesChannelViewAssign

    def build_task_kwargs(self, *, target):
        task_kwargs = super().build_task_kwargs(target=target)
        view_id = getattr(target.sales_channel_view, "id", target.sales_channel_view)
        if view_id:
            task_kwargs["sales_channel_view_id"] = view_id
            task_kwargs["view_id"] = view_id
        return task_kwargs


class EbayNonLiveMarketplaceViewAddTask(EbayMarketplaceViewAddTask):
    live = False
    product_task_fallback = resync_ebay_product_db_task


class EbaySingleViewAddTask(SingleViewAddTask, EbayChannelAddTask):
    pass


class EbayProductContentAddTask(ProductContentAddTask, EbayNonLiveMarketplaceViewAddTask):
    pass


class EbayProductPriceAddTask(ProductPriceAddTask, EbayNonLiveMarketplaceViewAddTask):
    pass


class EbayProductImagesAddTask(ProductImagesAddTask, EbayNonLiveMarketplaceViewAddTask):
    pass


class EbayProductDocumentsAddTask(ProductDocumentsAddTask, EbayNonLiveMarketplaceViewAddTask):
    def guard(self, *, target):
        guard_result = super().guard(target=target)
        if not guard_result.allowed:
            return guard_result

        if self.local_instance is None:
            return guard_result

        media = getattr(self.local_instance, "media", None)
        document_type_id = getattr(media, "document_type_id", None)
        if not document_type_id:
            return GuardResult(allowed=False, reason="document_type_missing")

        is_mapped = (
            EbayDocumentType.objects.filter(
                sales_channel=target.sales_channel,
                local_instance_id=document_type_id,
            )
            .exclude(remote_id__in=(None, ""))
            .exists()
        )
        if not is_mapped:
            return GuardResult(allowed=False, reason="ebay_document_type_not_mapped")

        return guard_result


class EbayProductPropertyAddTask(ProductPropertyAddTask, EbayNonLiveMarketplaceViewAddTask):
    def _get_category_id(self, *, view) -> str | None:
        from sales_channels.integrations.ebay.models import EbaySalesChannelView

        product = getattr(self, "product", None)
        if product is None or view is None:
            return None
        if not hasattr(view, "sales_channel"):
            view = EbaySalesChannelView.objects.get(id=view)
        if view is None:
            return None

        direct_remote_id = (
            EbayProductCategory.objects.filter(
                product=product,
                sales_channel=view.sales_channel,
                view=view,
            )
            .exclude(remote_id__in=(None, ""))
            .values_list("remote_id", flat=True)
            .first()
        )
        if direct_remote_id:
            candidate = str(direct_remote_id).strip()
            if candidate:
                return candidate


        product_type_remote_id = (
            EbayProductType.objects.filter(
                sales_channel=view.sales_channel,
                marketplace=view,
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

        if target.sales_channel_view is None:
            return GuardResult(allowed=False, reason="ebay_view_missing")

        product_property = self.local_instance
        property_obj = getattr(product_property, "property", None) if product_property else None
        if property_obj is None:
            return GuardResult(allowed=False, reason="ebay_property_missing")

        ebay_properties = EbayProperty.objects.filter(
            local_instance=property_obj,
            marketplace=target.sales_channel_view,
        )
        if not ebay_properties.exists():
            return GuardResult(allowed=False, reason="ebay_property_not_mapped")

        category_id = self._get_category_id(view=target.sales_channel_view)
        if not category_id:
            return GuardResult(allowed=False, reason="ebay_category_missing")

        if not EbayProductTypeItem.objects.filter(
            ebay_property__in=ebay_properties,
            product_type__remote_id=category_id,
            product_type__marketplace=target.sales_channel_view,
            product_type__sales_channel=target.sales_channel,
        ).exists():
            return GuardResult(allowed=False, reason="ebay_aspect_not_allowed_in_category")

        if property_obj.type in {property_obj.TYPES.SELECT, property_obj.TYPES.MULTISELECT}:
            if ebay_properties.filter(allows_unmapped_values=True).exists():
                return guard_result

            if property_obj.type == property_obj.TYPES.SELECT:
                select_value = getattr(product_property, "value_select", None)
                if select_value is None:
                    return GuardResult(allowed=False, reason="ebay_select_value_missing")
                is_mapped = EbayPropertySelectValue.objects.filter(
                    ebay_property__in=ebay_properties,
                    marketplace=target.sales_channel_view,
                    local_instance=select_value,
                ).exists()
                if not is_mapped:
                    return GuardResult(allowed=False, reason="ebay_select_value_unmapped")

            if property_obj.type == property_obj.TYPES.MULTISELECT:
                values = list(product_property.value_multi_select.all())
                if not values:
                    return GuardResult(allowed=False, reason="ebay_multiselect_value_missing")

                mapped_ids = set(
                    EbayPropertySelectValue.objects.filter(
                        ebay_property__in=ebay_properties,
                        marketplace=target.sales_channel_view,
                        local_instance__in=values,
                    ).values_list("local_instance_id", flat=True)
                )
                if any(value.id not in mapped_ids for value in values):
                    return GuardResult(allowed=False, reason="ebay_multiselect_value_unmapped")

        return guard_result


class EbayProductUpdateAddTask(ProductUpdateAddTask, EbayNonLiveMarketplaceViewAddTask):
    pass


class EbayProductEanCodeAddTask(ProductEanCodeAddTask, EbayNonLiveMarketplaceViewAddTask):
    pass
