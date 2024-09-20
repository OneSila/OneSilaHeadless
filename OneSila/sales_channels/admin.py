from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import RemoteTaskQueue, RemoteLog
from django.utils.translation import gettext_lazy as _

@admin.action(description=_("Retry selected tasks"))
def retry_task_action(modeladmin, request, queryset):
    for task in queryset:
        task.retry_task(retry_now=True)

@admin.register(RemoteTaskQueue)
class RemoteTaskQueueAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'status', 'priority', 'sent_to_queue_at_display']
    list_filter = ['status', 'sales_channel', 'task_name']

    actions = [retry_task_action]
    search_fields = ['task_name', 'sales_channel__hostname']

    fieldsets = (
        ('Task Information', {
            'fields': ('task_name', 'sales_channel', 'status', 'priority', 'retry', 'retry_button')
        }),
        ('Timing', {
            'fields': ('sent_to_queue_at',)
        }),
        ('Task Details', {
            'fields': ('task_args', 'task_kwargs', 'number_of_remote_requests')
        }),
        ('Error Details', {
            'fields': ('error_message', 'error_traceback')
        }),
    )

    def sent_to_queue_at_display(self, obj):
        return obj.sent_to_queue_at.strftime('%Y-%m-%d %H:%M:%S')
    sent_to_queue_at_display.short_description = 'Sent to Queue At'

    def retry_button(self, obj):
        return format_html(
            '<a class="button" href="{}">Retry Task</a>',
            reverse('sales_channels:retry_remote_task', args=[obj.id])
        )

    retry_button.short_description = 'Retry Task'
    retry_button.allow_tags = True

    readonly_fields = [
        'sales_channel', 'task_name', 'task_args', 'task_kwargs',
        'sent_to_queue_at', 'retry', 'error_message',
        'error_traceback', 'number_of_remote_requests', 'retry_button'
    ]

    def get_readonly_fields(self, request, obj=None):

        readonly = list(self.readonly_fields)
        if obj is not None:  # If editing an existing object
            return readonly
        return readonly


    def has_delete_permission(self, request, obj=None):
        # Allow deletion of tasks
        return True

@admin.register(RemoteLog)
class RemoteLogAdmin(admin.ModelAdmin):
    list_display = ('related_object_str', 'sales_channel', 'action', 'status', 'identifier', 'created_at')
    list_filter = ('status', 'action', 'sales_channel')
    search_fields = ('content_object__name', 'identifier')
    ordering = ('-created_at',)
    readonly_fields = ('payload', 'response', 'error_traceback', 'user_error', 'content_object', 'content_type', 'object_id', 'related_object_str', 'sales_channel', 'action', 'status', 'identifier', 'sales_channel')

    fieldsets = (
        (None, {
            'fields': ('related_object_str', 'content_type', 'object_id', 'content_object', 'sales_channel', 'action', 'status', 'identifier', 'multi_tenant_company')
        }),
        ('Details', {
            'fields': ('payload', 'response', 'error_traceback')
        }),
        ('Flags', {
            'fields': ('user_error', 'keep')
        }),
    )