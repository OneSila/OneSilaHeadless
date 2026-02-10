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
from sales_channels.integrations.ebay.models import (
    EbayProductCategory,
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


class EbayProductPropertyAddTask(ProductPropertyAddTask, EbayNonLiveMarketplaceViewAddTask):
    def get_sales_channels(self):
        channels = list(super().get_sales_channels())
        print(
            "EBAY_PRODUCT_PROPERTY TASK_GET_SALES_CHANNELS product_id=%s count=%s channel_ids=%s",
            getattr(getattr(self, "product", None), "id", None),
            len(channels),
            [getattr(c, "id", None) for c in channels],
        )
        for channel in channels:
            yield channel

    def get_targets(self, *, sales_channel):
        targets = list(super().get_targets(sales_channel=sales_channel))
        print(
            "EBAY_PRODUCT_PROPERTY TASK_GET_TARGETS sales_channel_id=%s product_id=%s count=%s targets=%s",
            getattr(sales_channel, "id", None),
            getattr(getattr(self, "product", None), "id", None),
            len(targets),
            [
                {
                    "remote_product_id": getattr(getattr(t, "remote_product", None), "id", None),
                    "view_id": getattr(getattr(t, "sales_channel_view", None), "id", getattr(t, "sales_channel_view", None)),
                }
                for t in targets
            ],
        )
        for target in targets:
            yield target

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
        print(
            "EBAY_PRODUCT_PROPERTY GUARD_START sales_channel_id=%s remote_product_id=%s view_id=%s local_instance_id=%s",
            getattr(getattr(target, "sales_channel", None), "id", None),
            getattr(getattr(target, "remote_product", None), "id", None),
            getattr(getattr(target, "sales_channel_view", None), "id", getattr(target, "sales_channel_view", None)),
            getattr(getattr(self, "local_instance", None), "id", None),
        )
        guard_result = super().guard(target=target)
        if not guard_result.allowed:
            print("EBAY_PRODUCT_PROPERTY GUARD_BLOCKED super reason=%s", guard_result.reason)
            return guard_result

        if target.sales_channel_view is None:
            print("EBAY_PRODUCT_PROPERTY GUARD_BLOCKED reason=ebay_view_missing")
            return GuardResult(allowed=False, reason="ebay_view_missing")

        product_property = self.local_instance
        property_obj = getattr(product_property, "property", None) if product_property else None
        if property_obj is None:
            print("EBAY_PRODUCT_PROPERTY GUARD_BLOCKED reason=ebay_property_missing")
            return GuardResult(allowed=False, reason="ebay_property_missing")

        ebay_properties = EbayProperty.objects.filter(
            local_instance=property_obj,
            marketplace=target.sales_channel_view,
        )
        if not ebay_properties.exists():
            print(
                "EBAY_PRODUCT_PROPERTY GUARD_BLOCKED reason=ebay_property_not_mapped property_id=%s view_id=%s",
                getattr(property_obj, "id", None),
                getattr(getattr(target, "sales_channel_view", None), "id", target.sales_channel_view),
            )
            return GuardResult(allowed=False, reason="ebay_property_not_mapped")

        category_id = self._get_category_id(view=target.sales_channel_view)
        if not category_id:
            print("EBAY_PRODUCT_PROPERTY GUARD_BLOCKED reason=ebay_category_missing")
            return GuardResult(allowed=False, reason="ebay_category_missing")

        if not EbayProductTypeItem.objects.filter(
            ebay_property__in=ebay_properties,
            product_type__remote_id=category_id,
            product_type__marketplace=target.sales_channel_view,
            product_type__sales_channel=target.sales_channel,
        ).exists():
            print("EBAY_PRODUCT_PROPERTY GUARD_BLOCKED reason=ebay_aspect_not_allowed_in_category category_id=%s", category_id)
            return GuardResult(allowed=False, reason="ebay_aspect_not_allowed_in_category")

        if property_obj.type in {property_obj.TYPES.SELECT, property_obj.TYPES.MULTISELECT}:
            if ebay_properties.filter(allows_unmapped_values=True).exists():
                return guard_result

            if property_obj.type == property_obj.TYPES.SELECT:
                select_value = getattr(product_property, "value_select", None)
                if select_value is None:
                    print("EBAY_PRODUCT_PROPERTY GUARD_BLOCKED reason=ebay_select_value_missing")
                    return GuardResult(allowed=False, reason="ebay_select_value_missing")
                is_mapped = EbayPropertySelectValue.objects.filter(
                    ebay_property__in=ebay_properties,
                    marketplace=target.sales_channel_view,
                    local_instance=select_value,
                ).exists()
                if not is_mapped:
                    print("EBAY_PRODUCT_PROPERTY GUARD_BLOCKED reason=ebay_select_value_unmapped select_value_id=%s", getattr(select_value, "id", None))
                    return GuardResult(allowed=False, reason="ebay_select_value_unmapped")

            if property_obj.type == property_obj.TYPES.MULTISELECT:
                values = list(product_property.value_multi_select.all())
                if not values:
                    print("EBAY_PRODUCT_PROPERTY GUARD_BLOCKED reason=ebay_multiselect_value_missing")
                    return GuardResult(allowed=False, reason="ebay_multiselect_value_missing")

                mapped_ids = set(
                    EbayPropertySelectValue.objects.filter(
                        ebay_property__in=ebay_properties,
                        marketplace=target.sales_channel_view,
                        local_instance__in=values,
                    ).values_list("local_instance_id", flat=True)
                )
                if any(value.id not in mapped_ids for value in values):
                    print("EBAY_PRODUCT_PROPERTY GUARD_BLOCKED reason=ebay_multiselect_value_unmapped values=%s mapped_ids=%s", [v.id for v in values], sorted(mapped_ids))
                    return GuardResult(allowed=False, reason="ebay_multiselect_value_unmapped")

        print("EBAY_PRODUCT_PROPERTY GUARD_ALLOWED remote_product_id=%s", getattr(getattr(target, "remote_product", None), "id", None))
        return guard_result


class EbayProductUpdateAddTask(ProductUpdateAddTask, EbayNonLiveMarketplaceViewAddTask):
    pass


class EbayProductEanCodeAddTask(ProductEanCodeAddTask, EbayNonLiveMarketplaceViewAddTask):
    pass
