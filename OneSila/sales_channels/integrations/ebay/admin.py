from django.contrib import admin

from .models import EbayCategory


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

