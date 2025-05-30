from django.contrib import admin
from core.admin import ModelAdmin
from .models import SalesPrice

# Register your models here.


@admin.register(SalesPrice)
class SalesPriceAdmin(ModelAdmin):
    pass
