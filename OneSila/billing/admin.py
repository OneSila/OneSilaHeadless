from django.contrib import admin
from core.admin import ModelAdmin
from .models import AiPointTransaction


@admin.register(AiPointTransaction)
class AiPointTransactionAdmin(ModelAdmin):
    list_display = ('created_at', 'multi_tenant_company', 'transaction_type', 'points')
    list_filter = ('transaction_type',)
    search_fields = ('multi_tenant_company__name',)
