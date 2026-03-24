import json

from django.contrib import admin
from django.urls import NoReverseMatch
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from core.admin import ModelAdmin
from .factories import MiraklPublicDefinitionSyncFactory
from .models import (
    MiraklCategory,
    MiraklProperty,
    MiraklSalesChannelFeedItem,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklPublicDefinition,
    MiraklSalesChannelFeed,
    MiraklSalesChannel,
)


@admin.action(description="Create Mirakl public definitions from undecided properties")
def sync_mirakl_public_definitions(modeladmin, request, queryset):
    total_synced = 0
    for sales_channel in queryset:
        total_synced += MiraklPublicDefinitionSyncFactory(sales_channel=sales_channel).run()
    modeladmin.message_user(
        request,
        f"Created or refreshed public definitions for {total_synced} Mirakl properties.",
    )


@admin.register(MiraklSalesChannel)
class MiraklSalesChannelAdmin(admin.ModelAdmin):
    list_display = ("hostname", "shop_id", "sub_type", "active", "representation_status")
    list_filter = ("active", "sub_type")
    search_fields = ("hostname", "shop_id")
    actions = (sync_mirakl_public_definitions,)

    @admin.display(description="Representation Status")
    def representation_status(self, obj):
        undecided = MiraklProperty.objects.filter(
            sales_channel=obj,
            representation_type_decided=False,
        ).count()
        if undecided:
            return f"{undecided} undecided"
        return "All decided"


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


class MiraklProductTypeItemInline(admin.StackedInline):
    model = MiraklProductTypeItem
    extra = 0
    fields = (
        "remote_property_code",
        "remote_property",
        "local_instance",
        "hierarchy_code",
        "requirement_level",
        "required",
        "variant",
        "role_data",
        "pretty_raw_data",
    )
    readonly_fields = fields
    show_change_link = True
    classes = ("collapse",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Property Code")
    def remote_property_code(self, obj):
        remote_property = getattr(obj, "remote_property", None)
        return getattr(remote_property, "code", None) or "-"

    @admin.display(description="Raw Data")
    def pretty_raw_data(self, obj):
        rendered = json.dumps(obj.raw_data or {}, indent=2, sort_keys=True, default=str)
        return format_html("<pre style='white-space: pre-wrap; max-width: 100%;'>{}</pre>", rendered)


class MiraklFeedItemInline(admin.StackedInline):
    model = MiraklSalesChannelFeedItem
    extra = 0
    fields = (
        "remote_product_link",
        "sales_channel_view",
        "action",
        "status",
        "identifier",
        "error_message",
        "pretty_payload_data",
        "pretty_result_data",
    )
    readonly_fields = fields
    show_change_link = False
    classes = ("collapse",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Remote Product")
    def remote_product_link(self, obj):
        remote_product = getattr(obj, "remote_product", None)
        if not getattr(remote_product, "pk", None):
            return "-"
        local_instance = getattr(remote_product, "local_instance", None)
        label = (
            getattr(local_instance, "sku", None)
            or getattr(remote_product, "remote_sku", None)
            or getattr(remote_product, "remote_id", None)
            or str(remote_product.pk)
        )
        app_label = remote_product._meta.app_label
        model_name = remote_product._meta.model_name
        try:
            url = reverse(f"admin:{app_label}_{model_name}_change", args=[remote_product.pk])
        except NoReverseMatch:
            return label
        return format_html('<a href="{}">{}</a>', url, label)

    @admin.display(description="Payload Data")
    def pretty_payload_data(self, obj):
        rendered = json.dumps(obj.payload_data or [], indent=2, sort_keys=True, default=str)
        return format_html("<pre style='white-space: pre-wrap; max-width: 100%;'>{}</pre>", rendered)

    @admin.display(description="Result Data")
    def pretty_result_data(self, obj):
        rendered = json.dumps(obj.result_data or {}, indent=2, sort_keys=True, default=str)
        return format_html("<pre style='white-space: pre-wrap; max-width: 100%;'>{}</pre>", rendered)


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


@admin.register(MiraklPublicDefinition)
class MiraklPublicDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "hostname",
        "property_code",
        "representation_type",
        "language",
        "default_value",
        "yes_text_value",
        "no_text_value",
    )
    list_filter = ("hostname", "representation_type")
    search_fields = ("hostname", "property_code")


@admin.register(MiraklSalesChannelFeed)
class MiraklSalesChannelFeedAdmin(ModelAdmin):
    actions = ("set_ready_to_render",)
    list_select_related = ("sales_channel", "multi_tenant_company")
    inlines = (MiraklFeedItemInline,)
    list_display = (
        "id",
        "sales_channel",
        "type",
        "stage",
        "status",
        "remote_id",
        "import_status",
        "reason_status",
        "last_synced_at",
        "created_at",
    )
    list_filter = ("type", "stage", "status", "import_status", "sales_channel")
    search_fields = (
        "remote_id",
        "product_remote_id",
        "offer_remote_id",
        "offer_import_remote_id",
        "import_status",
        "reason_status",
        "sales_channel__hostname",
    )
    raw_id_fields = ("sales_channel", "multi_tenant_company", "created_by_multi_tenant_user")
    ordering = ("-created_at",)
    readonly_fields = (
        "sales_channel",
        "multi_tenant_company",
        "type",
        "stage",
        "status",
        "remote_id",
        "product_remote_id",
        "offer_remote_id",
        "offer_import_remote_id",
        "import_status",
        "reason_status",
        "remote_date_created",
        "remote_shop_id",
        "conversion_type",
        "conversion_options_ai_enrichment_enabled",
        "conversion_options_ai_rewrite_enabled",
        "integration_details_invalid_products",
        "integration_details_products_not_accepted_in_time",
        "integration_details_products_not_synchronized_in_time",
        "integration_details_products_reimported",
        "integration_details_products_successfully_synchronized",
        "integration_details_products_with_synchronization_issues",
        "integration_details_products_with_wrong_identifiers",
        "integration_details_rejected_products",
        "has_error_report",
        "has_new_product_report",
        "has_transformation_error_report",
        "has_transformed_file",
        "transform_lines_read",
        "transform_lines_in_success",
        "transform_lines_in_error",
        "transform_lines_with_warning",
        "items_count",
        "rows_count",
        "file_link",
        "error_report_file_link",
        "new_product_report_file_link",
        "transformed_file_link",
        "transformation_error_report_file_link",
        "payload_data",
        "raw_data",
        "error_message",
        "last_synced_at",
        "last_submitted_at",
        "last_polled_at",
        "created_at",
        "updated_at",
        "created_by_multi_tenant_user",
        "last_update_by_multi_tenant_user",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "sales_channel",
                    "multi_tenant_company",
                    "type",
                    "stage",
                    "status",
                    "remote_id",
                    "product_remote_id",
                    "offer_remote_id",
                    "offer_import_remote_id",
                    "import_status",
                    "reason_status",
                    "remote_date_created",
                    "remote_shop_id",
                    "conversion_type",
                    "conversion_options_ai_enrichment_enabled",
                    "conversion_options_ai_rewrite_enabled",
                    "error_message",
                )
            },
        ),
        (
            "Integration Details",
            {
                "fields": (
                    "integration_details_invalid_products",
                    "integration_details_products_not_accepted_in_time",
                    "integration_details_products_not_synchronized_in_time",
                    "integration_details_products_reimported",
                    "integration_details_products_successfully_synchronized",
                    "integration_details_products_with_synchronization_issues",
                    "integration_details_products_with_wrong_identifiers",
                    "integration_details_rejected_products",
                )
            },
        ),
        (
            "Files",
            {
                "fields": (
                    "file_link",
                    "error_report_file_link",
                    "new_product_report_file_link",
                    "transformed_file_link",
                    "transformation_error_report_file_link",
                )
            },
        ),
        (
            "Report Flags",
            {
                "fields": (
                    "has_error_report",
                    "has_new_product_report",
                    "has_transformation_error_report",
                    "has_transformed_file",
                    "transform_lines_read",
                    "transform_lines_in_success",
                    "transform_lines_in_error",
                    "transform_lines_with_warning",
                    "items_count",
                    "rows_count",
                )
            },
        ),
        ("Payload", {"fields": ("payload_data", "raw_data")}),
        (
            "Timestamps",
            {
                "fields": (
                    "last_synced_at",
                    "last_submitted_at",
                    "last_polled_at",
                    "created_at",
                    "updated_at",
                    "created_by_multi_tenant_user",
                    "last_update_by_multi_tenant_user",
                )
            },
        ),
    )

    @admin.action(description="Set selected feeds to Ready To Render")
    def set_ready_to_render(self, request, queryset):
        updated = 0
        for feed in queryset.iterator():
            if feed.status == MiraklSalesChannelFeed.STATUS_READY_TO_RENDER:
                continue
            feed.status = MiraklSalesChannelFeed.STATUS_READY_TO_RENDER
            feed.save(update_fields=["status"])
            updated += 1

        self.message_user(
            request,
            f"Marked {updated} Mirakl feeds as ready to render.",
        )

    def has_add_permission(self, request):
        return False

    def _build_file_link(self, *, url: str | None, label: str) -> str:
        if not url:
            return "-"
        return format_html('<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>', url, label)

    @admin.display(description="Feed File")
    def file_link(self, obj):
        return self._build_file_link(url=obj.file_url, label="Open feed file")

    @admin.display(description="Error Report")
    def error_report_file_link(self, obj):
        return self._build_file_link(url=obj.error_report_file_url, label="Open error report")

    @admin.display(description="New Product Report")
    def new_product_report_file_link(self, obj):
        return self._build_file_link(url=obj.new_product_report_file_url, label="Open new product report")

    @admin.display(description="Transformed File")
    def transformed_file_link(self, obj):
        return self._build_file_link(url=obj.transformed_file_url, label="Open transformed file")

    @admin.display(description="Transformation Error Report")
    def transformation_error_report_file_link(self, obj):
        return self._build_file_link(
            url=obj.transformation_error_report_file_url,
            label="Open transformation error report",
        )


@admin.register(MiraklSalesChannelFeedItem)
class MiraklSalesChannelFeedItemAdmin(ModelAdmin):
    list_select_related = ("feed", "remote_product", "sales_channel_view")
    list_display = (
        "id",
        "feed",
        "remote_product_label",
        "sales_channel_view",
        "action",
        "status",
        "identifier",
    )
    list_filter = ("action", "status", "sales_channel_view", "feed__sales_channel")
    search_fields = (
        "identifier",
        "error_message",
        "remote_product__remote_sku",
        "remote_product__remote_id",
        "feed__remote_id",
        "feed__sales_channel__hostname",
    )
    raw_id_fields = ("feed", "remote_product", "sales_channel_view", "multi_tenant_company")
    readonly_fields = (
        "feed",
        "multi_tenant_company",
        "remote_product_link",
        "sales_channel_view",
        "action",
        "status",
        "identifier",
        "error_message",
        "pretty_payload_data",
        "pretty_result_data",
        "created_at",
        "updated_at",
        "created_by_multi_tenant_user",
        "last_update_by_multi_tenant_user",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "feed",
                    "multi_tenant_company",
                    "remote_product_link",
                    "sales_channel_view",
                    "action",
                    "status",
                    "identifier",
                    "error_message",
                )
            },
        ),
        ("Payload", {"fields": ("pretty_payload_data", "pretty_result_data")}),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "created_by_multi_tenant_user",
                    "last_update_by_multi_tenant_user",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description="Remote Product")
    def remote_product_label(self, obj):
        remote_product = getattr(obj, "remote_product", None)
        local_instance = getattr(remote_product, "local_instance", None)
        return (
            getattr(local_instance, "sku", None)
            or getattr(remote_product, "remote_sku", None)
            or getattr(remote_product, "remote_id", None)
            or "-"
        )

    @admin.display(description="Remote Product")
    def remote_product_link(self, obj):
        remote_product = getattr(obj, "remote_product", None)
        if not getattr(remote_product, "pk", None):
            return "-"
        label = self.remote_product_label(obj)
        app_label = remote_product._meta.app_label
        model_name = remote_product._meta.model_name
        try:
            url = reverse(f"admin:{app_label}_{model_name}_change", args=[remote_product.pk])
        except NoReverseMatch:
            return label
        return format_html('<a href="{}">{}</a>', url, label)

    @admin.display(description="Payload Data")
    def pretty_payload_data(self, obj):
        rendered = json.dumps(obj.payload_data or [], indent=2, sort_keys=True, default=str)
        return format_html("<pre style='white-space: pre-wrap; max-width: 100%;'>{}</pre>", rendered)

    @admin.display(description="Result Data")
    def pretty_result_data(self, obj):
        rendered = json.dumps(obj.result_data or {}, indent=2, sort_keys=True, default=str)
        return format_html("<pre style='white-space: pre-wrap; max-width: 100%;'>{}</pre>", rendered)
