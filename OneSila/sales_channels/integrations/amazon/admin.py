from django.contrib import admin

from core.admin import ModelAdmin
from sales_channels.admin import SalesChannelRemoteAdmin, SalesChannelRemoteProductAdmin
from polymorphic.admin import PolymorphicChildModelAdmin
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProductType,
    AmazonProductTypeItem,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProductProperty,
    AmazonSalesChannelView,
    AmazonRemoteLanguage,
    AmazonCurrency,
    AmazonOrder,
    AmazonOrderItem,
    AmazonProduct,
    AmazonProductContent,
    AmazonPrice,
    AmazonEanCode,
    AmazonImageProductAssociation,
    AmazonTaxCode,
    AmazonDefaultUnitConfigurator,
    AmazonImportRelationship, AmazonImportBrokenRecord,
    AmazonBrowseNode,
    AmazonProductBrowseNode,
    AmazonMerchantAsin,
    AmazonVariationTheme,
    AmazonGtinExemption, AmazonBrowseNode,
)
from sales_channels.integrations.amazon.models.properties import AmazonPublicDefinition
from django.contrib import admin
from django.utils.safestring import mark_safe
import json
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter


@admin.register(AmazonSalesChannel)
class AmazonSalesChannelAdmin(PolymorphicChildModelAdmin):
    base_model = AmazonSalesChannel
    list_display = ('hostname', 'region', 'active')
    list_filter = ('active', 'region')
    search_fields = ('hostname',)
    ordering = ('hostname',)

    fieldsets = (
        (None, {
            'fields': ('hostname', 'active', 'verify_ssl', 'region', 'refresh_token', 'first_import_complete', 'is_importing', 'multi_tenant_company')
        }),
        ('Amazon Settings', {
            'fields': ('use_configurable_name', 'sync_contents', 'sync_ean_codes', 'sync_prices', 'import_orders', 'requests_per_minute', 'max_retries')
        }),
    )


@admin.register(AmazonProperty)
class AmazonPropertyAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonPropertySelectValue)
class AmazonPropertySelectValueAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonProductProperty)
class AmazonProductPropertyAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonSalesChannelView)
class AmazonSalesChannelViewAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonRemoteLanguage)
class AmazonRemoteLanguageAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonCurrency)
class AmazonCurrencyAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonProductType)
class AmazonProductTypeAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonProductTypeItem)
class AmazonProductTypeItemAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonOrder)
class AmazonOrderAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonOrderItem)
class AmazonOrderItemAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonProduct)
class AmazonProductAdmin(SalesChannelRemoteProductAdmin):
    pass


@admin.register(AmazonProductContent)
class AmazonProductContentAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonPrice)
class AmazonPriceAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonEanCode)
class AmazonEanCodeAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonImageProductAssociation)
class AmazonImageProductAssociationAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonTaxCode)
class AmazonTaxCodeAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonDefaultUnitConfigurator)
class AmazonDefaultUnitConfiguratorAdmin(SalesChannelRemoteAdmin):
    pass


@admin.register(AmazonImportRelationship)
class AmazonImportRelationshipAdmin(admin.ModelAdmin):
    list_display = ("import_process", "parent_sku", "child_sku")
    search_fields = ("parent_sku", "child_sku")
    raw_id_fields = ("import_process",)


class CodeFilter(admin.SimpleListFilter):
    title = "code"
    parameter_name = "code"

    def lookups(self, request, model_admin):
        codes = model_admin.model.objects.values_list("record__code", flat=True).distinct()
        return [(code, code) for code in codes if code]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(record__code=self.value())
        return queryset


@admin.register(AmazonImportBrokenRecord)
class AmazonImportBrokenRecordAdmin(admin.ModelAdmin):
    list_display = ("import_process", "sku", "code")
    raw_id_fields = ("import_process",)
    list_filter = (CodeFilter,)
    search_fields = ("record__code",)

    readonly_fields = ["formatted_broken_record"]
    exclude = ("record",)

    def sku(self, instance):
        if not instance.record:
            return "-"
        data = instance.record.get("data", {}) or {}
        if isinstance(data, dict):
            sku = data.get("sku")
            if sku:
                return sku
        context = instance.record.get("context", {}) or {}
        if isinstance(context, dict):
            sku = context.get("sku")
            if sku:
                return sku
        return "-"

    def code(self, instance):
        if not instance.record:
            return "—"
        return instance.record.get("code", "—")

    def formatted_broken_record(self, instance):
        if not instance.record:
            return "—"

        response = json.dumps(instance.record, sort_keys=True, indent=2, ensure_ascii=False)
        formatter = HtmlFormatter(style="colorful")
        highlighted = highlight(response, JsonLexer(), formatter)

        # Clean up and apply inline style
        style = f"<style>{formatter.get_style_defs()}</style><br>"
        return mark_safe(style + highlighted.replace("\\n", "<br/>"))

    formatted_broken_record.short_description = "Broken Record"


@admin.register(AmazonPublicDefinition)
class AmazonPublicDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "api_region_code",
        "product_type_code",
        "code",
        "name",
        "is_required",
        "is_internal",
        "allowed_in_configurator",
        "last_fetched",
    )
    search_fields = ("code", "name", "product_type_code", "api_region_code")
    list_filter = ("api_region_code", "product_type_code", "is_required", "is_internal")
    readonly_fields = ("last_fetched",)
    ordering = ("api_region_code", "product_type_code", "code")
    fieldsets = (
        (None, {
            "fields": (
                "api_region_code",
                "product_type_code",
                "code",
                "name",
                "raw_schema",
                "export_definition",
                "usage_definition",
                "is_required",
                "is_internal",
                "allowed_in_configurator",
                "last_fetched",
            )
        }),
    )


@admin.register(AmazonBrowseNode)
class AmazonBrowseNodeAdmin(SalesChannelRemoteAdmin):
    list_display = (
        "remote_id",
        "name",
        "marketplace_id",
        "parent_node",
        "is_root",
        "has_children",
    )
    list_filter = ("is_root", "has_children", "marketplace_id")
    search_fields = ("remote_id",)
    raw_id_fields = ("parent_node",)


@admin.register(AmazonProductBrowseNode)
class AmazonProductBrowseNodeAdmin(admin.ModelAdmin):
    raw_id_fields = (
        "product",
        "sales_channel",
        "sales_channel_view",
        "multi_tenant_company",
        "created_by_multi_tenant_user",
    )


@admin.register(AmazonMerchantAsin)
class AmazonMerchantAsinAdmin(admin.ModelAdmin):
    raw_id_fields = (
        "product",
        "view",
        "multi_tenant_company",
        "created_by_multi_tenant_user",
    )


@admin.register(AmazonVariationTheme)
class AmazonVariationThemeAdmin(admin.ModelAdmin):
    raw_id_fields = (
        "product",
        "view",
        "multi_tenant_company",
        "created_by_multi_tenant_user",
    )


@admin.register(AmazonGtinExemption)
class AmazonGtinExemptionAdmin(admin.ModelAdmin):
    raw_id_fields = (
        "product",
        "view",
        "multi_tenant_company",
        "created_by_multi_tenant_user",
    )
