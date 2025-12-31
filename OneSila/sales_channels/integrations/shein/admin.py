from django.contrib import admin

from .models import SheinCategory


@admin.register(SheinCategory)
class SheinCategoryAdmin(admin.ModelAdmin):
    list_select_related = ("parent",)
    list_display = (
        "remote_id",
        "sales_channel",
        "name",
        "parent",
        "is_leaf",
        "product_type_remote_id",
        "updated_at",
    )
    list_filter = (
        "is_leaf",
        "sales_channel",
        "currency",
        "default_language",
        "reference_info_required",
        "reference_product_link_required",
        "proof_of_stock_required",
        "brand_code_required",
    )
    search_fields = (
        "remote_id",
        "name",
        "parent_remote_id",
        "product_type_remote_id",
    )
    raw_id_fields = ("parent",)
    ordering = ("sales_channel", "remote_id")
