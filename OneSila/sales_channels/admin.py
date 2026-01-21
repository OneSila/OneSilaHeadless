from django.contrib import admin
from django.contrib import messages
from django.db.models import TextField
from django.db.models.functions import Cast
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from polymorphic.admin import PolymorphicChildModelAdmin
from pygments.lexers import JsonLexer
from core.admin import ModelAdmin
from .models import SalesChannel, RemoteLog, SalesChannelImport, SalesChannelViewAssign, SalesChannelGptFeed, SyncRequest
from .models.products import RemoteProductConfigurator
import json
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter


def _enqueue_sync_requests(*, queryset):
    success_count = 0
    errors = []
    for sync_request in queryset:
        try:
            sync_request.enqueue()
            success_count += 1
        except Exception as exc:
            errors.append(f"SyncRequest {sync_request.pk}: {exc}")
    return success_count, errors


@admin.action(description=_("Enqueue selected sync requests"))
def enqueue_sync_requests_action(modeladmin, request, queryset):
    success_count, errors = _enqueue_sync_requests(queryset=queryset)
    if success_count:
        modeladmin.message_user(
            request,
            _("Enqueued %(count)s sync request(s).") % {"count": success_count},
            level=messages.SUCCESS,
        )
    if errors:
        modeladmin.message_user(
            request,
            _("Failed to enqueue %(count)s sync request(s).") % {"count": len(errors)},
            level=messages.ERROR,
        )

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


@admin.register(SalesChannelGptFeed)
class SalesChannelGptFeedAdmin(ModelAdmin):
    raw_id_fields = ['sales_channel']
    list_display = ('sales_channel', 'last_synced_at')


@admin.register(SyncRequest)
class SyncRequestAdmin(ModelAdmin):
    actions = [enqueue_sync_requests_action]
    list_display = (
        "id",
        "sync_type",
        "status",
        "sales_channel",
        "sales_channel_view",
        "remote_product_id",
        "task_func_path",
        "reason",
    )
    list_filter = (
        "status",
        "sync_type",
        "task_func_path",
        "reason",
        "sales_channel",
        "sales_channel_view",
    )
    search_fields = ("task_func_path", "reason")
    raw_id_fields = ("remote_product",)
    list_select_related = ("sales_channel", "sales_channel_view")
    readonly_fields = ("enqueue_button",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "remote_product",
                    "sales_channel",
                    "sales_channel_view",
                    "sync_type",
                    "status",
                    "reason",
                    "task_func_path",
                    "task_kwargs",
                    "number_of_remote_requests",
                    "enqueue_button",
                )
            },
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "enqueue/<int:sync_request_id>/",
                self.admin_site.admin_view(self.enqueue_sync_request),
                name="sales_channels_syncrequest_enqueue",
            ),
        ]
        return custom_urls + urls

    def enqueue_button(self, obj):
        if not obj:
            return "—"
        enqueue_url = reverse("admin:sales_channels_syncrequest_enqueue", args=[obj.id])
        return format_html('<a class="button" href="{}">Enqueue</a>', enqueue_url)

    enqueue_button.short_description = "Enqueue"
    enqueue_button.allow_tags = True

    def enqueue_sync_request(self, request, sync_request_id):
        sync_request = self.get_object(request, sync_request_id)
        if not sync_request:
            self.message_user(request, _("Sync request not found."), level=messages.ERROR)
            redirect_url = request.META.get("HTTP_REFERER") or reverse("admin:sales_channels_syncrequest_changelist")
            return HttpResponseRedirect(redirect_url)

        try:
            sync_request.enqueue()
            self.message_user(request, _("Sync request enqueued."), level=messages.SUCCESS)
        except Exception as exc:
            self.message_user(
                request,
                _("Failed to enqueue sync request: %(error)s") % {"error": exc},
                level=messages.ERROR,
            )
        redirect_url = request.META.get("HTTP_REFERER") or reverse("admin:sales_channels_syncrequest_changelist")
        return HttpResponseRedirect(redirect_url)

    def get_search_results(self, request, queryset, search_term):
        base_queryset = queryset
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if not search_term:
            return queryset, use_distinct

        task_kwargs_queryset = base_queryset.annotate(
            task_kwargs_text=Cast("task_kwargs", output_field=TextField())
        ).filter(task_kwargs_text__icontains=search_term)
        return queryset | task_kwargs_queryset, use_distinct
