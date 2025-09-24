from django.contrib import admin

from .models import EbayCategory


@admin.register(EbayCategory)
class EbayCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "remote_id", "marketplace_default_tree_id")
    list_filter = ("marketplace_default_tree_id",)
    search_fields = ("name", "remote_id")
