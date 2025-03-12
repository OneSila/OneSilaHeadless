from django.contrib import admin
from polymorphic.admin import PolymorphicChildModelAdmin
from pygments.lexers import JsonLexer

from .models import SalesChannel, RemoteLog
from .models.products import RemoteProductConfigurator


@admin.register(RemoteProductConfigurator)
class RemoteProductConfiguratorAdmin(admin.ModelAdmin):
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
    readonly_fields = ['payload', 'response', 'error_traceback', 'user_error', 'content_object', 'content_type', 'object_id', 'related_object_str', 'integration', 'action', 'status', 'identifier', 'fixing_identifier', 'remote_product']

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