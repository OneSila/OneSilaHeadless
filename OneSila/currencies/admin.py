from django.contrib import admin
from currencies.models import PublicCurrency, Currency

# Register your models here.

@admin.register(PublicCurrency)
class PublicCurrencyAdmin(admin.ModelAdmin):
    pass

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    pass
