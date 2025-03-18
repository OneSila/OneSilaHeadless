from django.contrib import admin
from .models import AiGenerateProcess, AiTranslationProcess


@admin.register(AiGenerateProcess)
class AiGenerateProcessAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction', 'cost', 'result_time')
    list_filter = ('transaction__transaction_type',)
    search_fields = ('product__name', 'prompt', 'result')

@admin.register(AiTranslationProcess)
class AiTranslationProcessAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'cost', 'result_time', 'from_language_code', 'to_language_code')
    list_filter = ('transaction__transaction_type', 'from_language_code', 'to_language_code')
    search_fields = ('translate_from', 'result')