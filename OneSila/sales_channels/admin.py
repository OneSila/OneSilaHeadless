from django.contrib import admin
from polymorphic.admin import PolymorphicChildModelAdmin
from pygments.lexers import JsonLexer
from core.admin import ModelAdmin
from .models import SalesChannel, RemoteLog, SalesChannelImport, SalesChannelViewAssign
from .models.products import RemoteProductConfigurator
from django.utils.safestring import mark_safe
import json
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

@admin.register(RemoteProductConfigurator)
class RemoteProductConfiguratorAdmin(ModelAdmin):
    pass


@admin.register(SalesChannel)
class SalesChannelAdmin(PolymorphicChildModelAdmin):
    base_model = SalesChannel


@admin.register(RemoteLog)
class RemoteLogAdmin(PolymorphicChildModelAdmin):
    base_model = RemoteLog
    list_display = ('related_object_str', 'integration', 'action', 'status', 'identifier', 'created_at')
    list_filter = ('status', 'action', 'integration')
    search_fields = ('content_object__name', 'identifier')
    ordering = ('-created_at',)
    readonly_fields = ['payload', 'response', 'error_traceback', 'user_error', 'content_object', 'content_type', 'object_id',
        'related_object_str', 'integration', 'action', 'status', 'identifier', 'fixing_identifier', 'remote_product']

    fieldsets = (
        (None, {
            'fields': ('related_object_str', 'content_type', 'object_id', 'content_object', 'integration', 'remote_product', 'action', 'status', 'identifier', 'fixing_identifier', 'multi_tenant_company')
        }),
        ('Details', {
            'fields': ('payload', 'response', 'error_traceback')
        }),
        ('Flags', {
            'fields': ('user_error', 'keep')
        }),
    )


@admin.register(SalesChannelImport)
class SalesChannelImportAdmin(ModelAdmin):
    raw_id_fields = [
        'sales_channel',
        'multi_tenant_company',
        'created_by_multi_tenant_user',
    ]

    readonly_fields = ['formatted_broken_records']
    exclude = ('broken_records',)

    def formatted_broken_records(self, instance):
        if not instance.broken_records:
            return "—"

        response = json.dumps(instance.broken_records, sort_keys=True, indent=2, ensure_ascii=False)
        formatter = HtmlFormatter(style='colorful')
        highlighted = highlight(response, JsonLexer(), formatter)

        # Clean up and apply inline style
        style = f"<style>{formatter.get_style_defs()}</style><br>"
        return mark_safe(style + highlighted.replace('\\n', '<br/>'))

    formatted_broken_records.short_description = 'Broken Records'


class SalesChannelRemoteAdmin(ModelAdmin):
    raw_id_fields = [
        'multi_tenant_company',
        'created_by_multi_tenant_user',
        'sales_channel',
    ]


class SalesChannelRemoteProductAdmin(ModelAdmin):
    raw_id_fields = [
        'multi_tenant_company',
        'created_by_multi_tenant_user',
        'sales_channel',
        'local_instance',
    ]


@admin.register(SalesChannelViewAssign)
class SalesChannelViewAssignAdmin(SalesChannelRemoteAdmin):
    raw_id_fields = [
        'sales_channel',
        'product',
        'remote_product',
        'sales_channel_view',
        'created_by_multi_tenant_user',
        'last_update_by_multi_tenant_user',
        'multi_tenant_company',
    ]
