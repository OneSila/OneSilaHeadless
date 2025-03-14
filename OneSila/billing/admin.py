from django.contrib import admin
from .models import AiPointTransaction, AiPointContentGenerateProcess


@admin.register(AiPointTransaction)
class AiPointTransactionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'multi_tenant_company', 'transaction_type', 'points')
    list_filter = ('transaction_type',)
    search_fields = ('multi_tenant_company__name',)


@admin.register(AiPointContentGenerateProcess)
class AiPointContentGenerateProcessAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction', 'cost', 'result_time')
    list_filter = ('transaction__transaction_type',)
    search_fields = ('product__name', 'prompt', 'result')
