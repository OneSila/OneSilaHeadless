from django.contrib import admin

from .models import SheinCategory


@admin.register(SheinCategory)
class SheinCategoryAdmin(admin.ModelAdmin):
    list_select_related = ("parent",)
    list_display = (
        "remote_id",
        "site_abbr",
        "site_domain_guess",
        "name",
        "parent",
        "is_leaf",
        "product_type_remote_id",
        "updated_at",
    )
    list_filter = (
        "is_leaf",
        "site_remote_id",
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
        "site_remote_id",
        "parent_remote_id",
        "product_type_remote_id",
    )
    raw_id_fields = ("parent",)
    ordering = ("site_remote_id", "remote_id")

    @admin.display(description="Site (abbr)")
    def site_abbr(self, obj: SheinCategory) -> str:
        return (obj.site_remote_id or "").strip()

    @admin.display(description="Site (domain)")
    def site_domain_guess(self, obj: SheinCategory) -> str:
        value = (obj.site_remote_id or "").strip().lower()
        if not value:
            return ""
        if value == "shein":
            return "shein.com"
        if value.startswith("shein-"):
            suffix = value.split("shein-", 1)[1]
            if suffix:
                return f"{suffix}.shein.com"
        return ""
