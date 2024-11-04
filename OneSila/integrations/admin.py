from django.contrib import admin
from polymorphic.admin import PolymorphicChildModelFilter, PolymorphicParentModelAdmin

from integrations.models import Integration, IntegrationTaskQueue, IntegrationLog
from django.urls import path, reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib import messages
import json
from django.contrib import admin
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.models import SalesChannel, RemoteLog


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
class RemoteTaskQueueAdmin(admin.ModelAdmin):
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
    child_models = (RemoteLog, )
    list_display = ('related_object_str', 'integration', 'action', 'status', 'identifier', 'created_at')
    list_filter = ('status', 'action', 'integration', PolymorphicChildModelFilter)
    search_fields = ('content_object__name', 'identifier')
    ordering = ('-created_at',)
    fields = ['payload', 'response', 'error_traceback', 'user_error', 'content_object', 'content_type', 'object_id', 'related_object_str', 'integration', 'action', 'status', 'identifier']
    readonly_fields = ['payload', 'response', 'error_traceback', 'user_error', 'content_object', 'content_type', 'object_id', 'related_object_str', 'integration', 'action', 'status', 'identifier']

    base_fieldsets = (
        (None, {
            'fields': ('related_object_str', 'content_type', 'object_id', 'content_object', 'integration', 'action', 'status', 'identifier', 'multi_tenant_company')
        }),
        ('Details', {
            'fields': ('payload', 'response', 'error_traceback')
        }),
        ('Flags', {
            'fields': ('user_error', 'keep')
        }),
    )