from django.contrib import admin
from core.admin import ModelAdmin, SharedModelAdmin
from polymorphic.admin import PolymorphicChildModelFilter, PolymorphicParentModelAdmin

from integrations.models import (
    Integration,
    IntegrationTaskQueue,
    IntegrationLog,
    PublicIntegrationType,
    PublicIntegrationTypeTranslation,
    PublicIssue,
    PublicIssueCategory,
    PublicIssueImage,
    PublicIssueRequest,
)
from django.urls import path, reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.db.models import Q
import json
from urllib.parse import urlencode

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, ngettext

from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.models import SalesChannel, RemoteLog


class PublicIntegrationTypeTranslationInline(admin.TabularInline):
    model = PublicIntegrationTypeTranslation
    extra = 1


class PublicIssueCategoryInline(admin.TabularInline):
    model = PublicIssueCategory
    extra = 1


class PublicIssueImageInline(admin.TabularInline):
    model = PublicIssueImage
    extra = 1


class _BaseLogoPresenceFilter(admin.SimpleListFilter):
    title = ""
    parameter_name = ""
    field_name = ""

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.exclude(**{f"{self.field_name}__isnull": True}).exclude(**{self.field_name: ""})
        if value == "no":
            return queryset.filter(Q(**{f"{self.field_name}__isnull": True}) | Q(**{self.field_name: ""}))
        return queryset


class HasPngFilter(_BaseLogoPresenceFilter):
    title = _("has_png")
    parameter_name = "has_png"
    field_name = "logo_png"


class HasSvgFilter(_BaseLogoPresenceFilter):
    title = _("has_svg")
    parameter_name = "has_svg"
    field_name = "logo_svg"


@admin.register(Integration)
class IntegrationAdmin(PolymorphicParentModelAdmin):
    base_model = Integration
    list_filter = (PolymorphicChildModelFilter,)
    child_models = (SalesChannel, MagentoSalesChannel)


@admin.action(description=_("Retry selected tasks"))
def retry_task_action(modeladmin, request, queryset):
    for task in queryset:
        task.retry_task(retry_now=True)


@admin.register(IntegrationTaskQueue)
class RemoteTaskQueueAdmin(ModelAdmin):
    list_display = ['__str__', 'status', 'priority', 'sent_to_queue_at_display']
    list_filter = ['status', 'integration', 'task_name']
    actions = [retry_task_action]
    search_fields = ['task_name', 'integration__hostname']

    fieldsets = (
        ('Task Information', {
            'fields': ('task_name', 'integration', 'status', 'priority', 'retry', 'retry_button')
        }),
        ('Timing', {
            'fields': ('sent_to_queue_at',)
        }),
        ('Task Details', {
            'fields': ('task_args', 'task_kwargs', 'number_of_remote_requests')
        }),
        ('Error Details', {
            'fields': ('error_message', 'error_traceback', 'history')
        }),
    )

    def sent_to_queue_at_display(self, obj):
        return obj.sent_to_queue_at.strftime('%Y-%m-%d %H:%M:%S')
    sent_to_queue_at_display.short_description = 'Sent to Queue At'

    def retry_button(self, obj):
        # Generate a URL for the custom admin action using the correct view name
        retry_url = reverse('admin:integrations_integrationtaskqueue_retry', args=[obj.id])
        return format_html(
            '<a class="button" href="{}">Retry Task</a>',
            retry_url
        )

    retry_button.short_description = 'Retry Task'
    retry_button.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'retry-task/<int:task_id>/',
                self.admin_site.admin_view(self.retry_task),
                name='integrations_integrationtaskqueue_retry'
            ),
        ]
        return custom_urls + urls

    def retry_task(self, request, task_id):
        """
        Custom admin view to retry a specific task.
        """
        task = get_object_or_404(IntegrationTaskQueue, id=task_id)
        try:
            task.retry_task(retry_now=True)
            self.message_user(request, f"Task {task.task_name} has been retried successfully.")
        except Exception as e:
            self.message_user(request, f"Failed to retry task {task.task_name}: {e}", level=messages.ERROR)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    def history(self, instance):
        response = json.dumps(instance.error_history, sort_keys=True, indent=2)
        formatter = HtmlFormatter(style='colorful')
        response = highlight(response, JsonLexer(), formatter)

        response = response.replace('\\n', '<br/>').replace('\"', '').replace('\"', '')
        style = "<style>" + formatter.get_style_defs() + "</style><br>"

        return mark_safe(style + response)
    history.short_description = 'Error History'

    readonly_fields = [
        'integration', 'task_name', 'task_args', 'task_kwargs',
        'sent_to_queue_at', 'retry', 'error_message',
        'error_traceback', 'number_of_remote_requests', 'retry_button', 'history'
    ]

    def get_readonly_fields(self, request, obj=None):

        readonly = list(self.readonly_fields)
        if obj is not None:  # If editing an existing object
            return readonly
        return readonly

    def has_delete_permission(self, request, obj=None):
        # Allow deletion of tasks
        return True


@admin.register(IntegrationLog)
class IntegrationLogAdmin(PolymorphicParentModelAdmin):
    base_model = IntegrationLog
    child_models = (IntegrationLog, RemoteLog)
    list_display = ('related_object_str', 'integration', 'action', 'status', 'identifier', 'created_at')
    list_filter = ('status', 'action', 'integration', PolymorphicChildModelFilter)
    search_fields = ('content_object__name', 'identifier')
    ordering = ('-created_at',)
    fields = ['payload', 'response', 'error_traceback', 'user_error', 'content_object', 'content_type',
        'object_id', 'related_object_str', 'integration', 'remote_product', 'action', 'status', 'identifier']
    readonly_fields = ['payload', 'response', 'error_traceback', 'user_error', 'content_object', 'content_type',
        'object_id', 'related_object_str', 'integration', 'action', 'status', 'identifier', 'remote_product']

    base_fieldsets = (
        (None, {
            'fields': ('related_object_str', 'content_type', 'object_id', 'content_object', 'integration', 'remote_product', 'action', 'status', 'identifier', 'multi_tenant_company')
        }),
        ('Details', {
            'fields': ('payload', 'response', 'error_traceback')
        }),
        ('Flags', {
            'fields': ('user_error', 'keep')
        }),
    )


@admin.register(PublicIntegrationType)
class PublicIntegrationTypeAdmin(SharedModelAdmin):
    list_display = (
        "display_name",
        "key",
        "type",
        "subtype",
        "category",
        "based_to",
        "active",
        "is_beta",
        "supports_open_ai_product_feed",
        "sort_order",
    )
    list_filter = ("category", "active", "is_beta", "supports_open_ai_product_feed", HasPngFilter, HasSvgFilter)
    search_fields = ("key", "type", "subtype", "translations__name", "translations__description")
    raw_id_fields = ("based_to",)
    inlines = (PublicIntegrationTypeTranslationInline,)
    ordering = ("sort_order", "key")
    list_select_related = ("based_to",)
    actions = ("enable_selected", "disable_selected")

    @admin.action(description=_("Enable selected public integration types"))
    def enable_selected(self, request, queryset):
        updated_count = queryset.update(active=True)
        self.message_user(
            request,
            ngettext(
                "%(count)s public integration type was enabled.",
                "%(count)s public integration types were enabled.",
                updated_count,
            ) % {"count": updated_count},
        )

    @admin.action(description=_("Disable selected public integration types"))
    def disable_selected(self, request, queryset):
        updated_count = queryset.update(active=False)
        self.message_user(
            request,
            ngettext(
                "%(count)s public integration type was disabled.",
                "%(count)s public integration types were disabled.",
                updated_count,
            ) % {"count": updated_count},
        )

    @admin.display(description="Name")
    def display_name(self, obj):
        return obj.name(language=None) or "-"


@admin.register(PublicIntegrationTypeTranslation)
class PublicIntegrationTypeTranslationAdmin(SharedModelAdmin):
    list_display = ("name", "language", "public_integration_type")
    list_filter = ("language",)
    search_fields = ("name", "description", "public_integration_type__key")
    raw_id_fields = ("public_integration_type",)
    list_select_related = ("public_integration_type",)


@admin.register(PublicIssue)
class PublicIssueAdmin(SharedModelAdmin):
    list_display = ("code", "integration_type", "short_issue", "request_reference", "created_at")
    list_filter = ("integration_type__category", "integration_type")
    search_fields = (
        "code",
        "issue",
        "cause",
        "recommended_fix",
        "=request_reference",
        "integration_type__key",
        "integration_type__type",
        "integration_type__subtype",
        "categories__name",
        "categories__code",
    )
    raw_id_fields = ("integration_type",)
    list_select_related = ("integration_type",)
    inlines = (PublicIssueCategoryInline, PublicIssueImageInline)

    @admin.display(description="Issue")
    def short_issue(self, obj):
        return obj.issue[:120]


@admin.register(PublicIssueRequest)
class PublicIssueRequestAdmin(ModelAdmin):
    list_display = (
        "short_issue",
        "integration_type",
        "submission_id",
        "product_sku",
        "status",
        "multi_tenant_company",
        "created_at",
    )
    list_filter = ("status", "integration_type", "multi_tenant_company")
    search_fields = (
        "issue",
        "description",
        "submission_id",
        "product_sku",
        "status",
        "integration_type__key",
        "integration_type__type",
        "integration_type__subtype",
    )
    raw_id_fields = ("integration_type",)
    list_select_related = ("integration_type", "multi_tenant_company")
    readonly_fields = (
        "multi_tenant_company",
        "created_by_multi_tenant_user",
        "last_update_by_multi_tenant_user",
        "created_at",
        "updated_at",
        "create_public_issue_button",
    )

    @admin.display(description="Issue")
    def short_issue(self, obj):
        return obj.issue[:120]

    @admin.display(description="Create Public Issue")
    def create_public_issue_button(self, obj):
        if not obj or not obj.pk:
            return "-"

        add_url = reverse("admin:integrations_publicissue_add")
        query = urlencode(
            {
                "integration_type": obj.integration_type_id,
                "request_reference": obj.pk,
                "issue": obj.issue,
            }
        )
        return format_html('<a class="button" href="{}?{}">Create Public Issue</a>', add_url, query)
