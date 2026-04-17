from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _, ngettext

from core.admin import ModelAdmin

from .models import AiGenerateProcess, AiTranslationProcess, AiImportProcess, McpApiKey, McpToolRun


@admin.action(description=_("Regenerate selected MCP API keys"))
def regenerate_mcp_api_keys(modeladmin, request, queryset):
    regenerated_count = 0

    for mcp_api_key in queryset:
        mcp_api_key.regenerate_key(save=True)
        regenerated_count += 1

    modeladmin.message_user(
        request,
        ngettext(
            "%d MCP API key was regenerated.",
            "%d MCP API keys were regenerated.",
            regenerated_count,
        ) % regenerated_count,
        level=messages.SUCCESS,
    )


@admin.register(McpApiKey)
class McpApiKeyAdmin(ModelAdmin):
    list_display = ("multi_tenant_company", "key", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("multi_tenant_company__name", "key")
    list_select_related = ("multi_tenant_company",)
    raw_id_fields = ("multi_tenant_company",)
    ordering = ("multi_tenant_company__name",)
    actions = (regenerate_mcp_api_keys,)
    readonly_fields = ("key", "created_at", "updated_at")
    fields = ("multi_tenant_company", "key", "is_active", "created_at", "updated_at")


@admin.register(AiGenerateProcess)
class AiGenerateProcessAdmin(ModelAdmin):
    list_display = ('product', 'transaction', 'cost', 'result_time')
    list_filter = ('transaction__transaction_type',)
    search_fields = ('product__name', 'prompt', 'result')


@admin.register(AiTranslationProcess)
class AiTranslationProcessAdmin(ModelAdmin):
    list_display = ('transaction', 'cost', 'result_time', 'from_language_code', 'to_language_code')
    list_filter = ('transaction__transaction_type', 'from_language_code', 'to_language_code')
    search_fields = ('translate_from', 'result')


@admin.register(AiImportProcess)
class AiImportProcessAdmin(ModelAdmin):
    list_display = ('transaction', 'get_type_display', 'cost', 'result_time')
    list_filter = ('transaction__transaction_type', 'type')
    search_fields = ('prompt', 'result')


@admin.register(McpToolRun)
class McpToolRunAdmin(ModelAdmin):
    list_display = ("tool_name", "multi_tenant_company", "status", "percentage", "created_at")
    list_filter = ("tool_name", "status")
    search_fields = ("tool_name", "name", "multi_tenant_company__name")
    list_select_related = ("multi_tenant_company",)
    raw_id_fields = ("multi_tenant_company",)
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "multi_tenant_company",
        "tool_name",
        "name",
        "status",
        "percentage",
        "create_only",
        "update_only",
        "override_only",
        "skip_broken_records",
        "total_records",
        "processed_records",
        "assigned_views",
        "payload_content",
        "response_content",
        "broken_records",
        "error_traceback",
        "created_at",
        "updated_at",
    )
