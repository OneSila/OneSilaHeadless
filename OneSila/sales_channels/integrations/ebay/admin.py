from django.contrib import admin

from .models import EbayCategory, EbayProduct, EbayProductOffer


@admin.register(EbayCategory)
class EbayCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "name",
        "remote_id",
        "marketplace_default_tree_id",
        "is_root",
        "has_children",
    )
    list_filter = ("marketplace_default_tree_id", "is_root", "has_children")
    search_fields = ("full_name", "name", "remote_id")
    raw_id_fields = ('parent_node',)


@admin.register(EbayProductOffer)
class EbayProductOfferAdmin(admin.ModelAdmin):
    list_display = (
        "remote_id",
        "get_local_product_display",
        "sales_channel_view",
        "listing_id",
        "listing_status",
        "sales_channel",
    )
    list_filter = ("sales_channel_view__sales_channel", "listing_status")
    search_fields = (
        "remote_id",
        "listing_id",
        "remote_product__remote_sku",
        "remote_product__local_instance__sku",
        "remote_product__local_instance__name",
        "sales_channel_view__name",
        "sales_channel_view__remote_id",
    )
    raw_id_fields = (
        "remote_product",
        "sales_channel_view",
        "sales_channel",
        "multi_tenant_company",
    )
    list_select_related = (
        "remote_product",
        "remote_product__local_instance",
        "sales_channel_view",
        "sales_channel_view__sales_channel",
    )

    @admin.display(description="Product")
    def get_local_product_display(self, obj):
        remote_product = getattr(obj, "remote_product", None)
        if not remote_product:
            return "-"

        local_instance = getattr(remote_product, "local_instance", None)
        if local_instance:
            sku = getattr(local_instance, "sku", None) or "N/A"
            name = getattr(local_instance, "name", "") or ""
            return f"{sku} {name}".strip()

        return getattr(remote_product, "remote_sku", None) or str(remote_product)


@admin.register(EbayProduct)
class EbayProductAdmin(admin.ModelAdmin):
    list_display = (
        "remote_sku",
        "get_local_product_display",
        "sales_channel",
        "is_variation",
        "status",
    )
    list_filter = ("sales_channel", "status", "is_variation")
    search_fields = (
        "remote_sku",
        "remote_id",
        "local_instance__sku",
        "local_instance__name",
    )
    raw_id_fields = (
        "local_instance",
        "remote_parent_product",
        "sales_channel",
        "multi_tenant_company",
    )
    list_select_related = (
        "local_instance",
        "sales_channel",
        "remote_parent_product",
    )

    @admin.display(description="Product")
    def get_local_product_display(self, obj):
        local_instance = getattr(obj, "local_instance", None)
        if local_instance:
            sku = getattr(local_instance, "sku", "") or ""
            name = getattr(local_instance, "name", "") or ""
            label = f"{sku} {name}".strip()
            return label or sku or name or "-"
        return "-"
