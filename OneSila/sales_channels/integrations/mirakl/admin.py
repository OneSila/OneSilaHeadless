from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from .models import MiraklCategory, MiraklProductType, MiraklProductTypeItem


class MiraklProductTypeInline(admin.TabularInline):
    model = MiraklProductType
    extra = 0
    fields = ("product_type_link", "name", "local_instance", "template", "ready_to_push", "imported", "updated_at")
    readonly_fields = fields
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Product Type")
    def product_type_link(self, obj):
        if not obj.pk:
            return "-"
        url = reverse("admin:mirakl_miraklproducttype_change", args=[obj.pk])
        label = obj.remote_id or obj.name or str(obj.pk)
        return format_html('<a href="{}">{}</a>', url, label)

    @admin.display(boolean=True, description="Ready To Push")
    def ready_to_push(self, obj):
        return obj.ready_to_push


class MiraklProductTypeItemInline(admin.TabularInline):
    model = MiraklProductTypeItem
    extra = 0
    fields = ("remote_property_code", "remote_property", "local_instance", "required", "variant", "role_data")
    readonly_fields = fields
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Property Code")
    def remote_property_code(self, obj):
        remote_property = getattr(obj, "remote_property", None)
        return getattr(remote_property, "code", None) or "-"


@admin.register(MiraklCategory)
class MiraklCategoryAdmin(admin.ModelAdmin):
    list_select_related = ("sales_channel", "parent")
    list_display = (
        "remote_id",
        "sales_channel",
        "name",
        "parent",
        "level",
        "is_leaf",
        "get_product_types",
        "updated_at",
    )
    list_filter = ("sales_channel", "is_leaf", "level")
    search_fields = ("remote_id", "name", "parent_code")
    raw_id_fields = ("sales_channel", "multi_tenant_company", "parent")
    ordering = ("sales_channel", "level", "remote_id")
    readonly_fields = ("product_types_links",)
    inlines = (MiraklProductTypeInline,)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "sales_channel",
                    "multi_tenant_company",
                    "remote_id",
                    "name",
                    "parent_code",
                    "parent",
                    "level",
                    "is_leaf",
                    "raw_data",
                    "product_types_links",
                )
            },
        ),
    )

    @admin.display(description="Product Types")
    def get_product_types(self, obj):
        product_types = list(obj.product_types.values_list("remote_id", flat=True)[:5])
        if not product_types:
            return "-"
        suffix = "" if obj.product_types.count() <= 5 else " ..."
        return ", ".join(product_types) + suffix

    @admin.display(description="Product Type Links")
    def product_types_links(self, obj):
        product_types = obj.product_types.all().order_by("remote_id")
        if not product_types.exists():
            return "-"
        return format_html_join(
            format_html("<br>"),
            '<a href="{}">{}</a>',
            (
                (
                    reverse("admin:mirakl_miraklproducttype_change", args=[product_type.pk]),
                    product_type.remote_id or product_type.name or str(product_type.pk),
                )
                for product_type in product_types
            ),
        )


@admin.register(MiraklProductType)
class MiraklProductTypeAdmin(admin.ModelAdmin):
    list_select_related = ("sales_channel", "category", "local_instance")
    list_display = (
        "remote_id",
        "name",
        "sales_channel",
        "category",
        "local_instance",
        "ready_to_push",
        "imported",
        "updated_at",
    )
    list_filter = ("sales_channel", "imported")
    search_fields = ("remote_id", "name", "category__remote_id", "category__name")
    raw_id_fields = ("sales_channel", "multi_tenant_company", "category", "local_instance")
    ordering = ("sales_channel", "remote_id")
    inlines = (MiraklProductTypeItemInline,)
    readonly_fields = ("ready_to_push", "template_url")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "sales_channel",
                    "multi_tenant_company",
                    "remote_id",
                    "name",
                    "category",
                    "local_instance",
                    "template",
                    "template_url",
                    "ready_to_push",
                    "imported",
                )
            },
        ),
    )

    @admin.display(boolean=True, description="Ready To Push")
    def ready_to_push(self, obj):
        return obj.ready_to_push
