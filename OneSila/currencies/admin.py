from django.contrib import admin
from core.admin import ModelAdmin, SharedModelAdmin
from currencies.models import PublicCurrency, Currency

# Register your models here.


@admin.register(PublicCurrency)
class PublicCurrencyAdmin(SharedModelAdmin):
    pass


@admin.register(Currency)
class CurrencyAdmin(ModelAdmin):
    pass
