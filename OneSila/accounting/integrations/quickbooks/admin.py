from django.contrib import admin

from accounting.integrations.quickbooks.models import QuickbooksAccount


@admin.register(QuickbooksAccount)
class QuickbooksAccountAdmin(admin.ModelAdmin):
    pass