from django.contrib import admin
from .models import SalesPrice

# Register your models here.


@admin.register(SalesPrice)
class SalesPriceAdmin(admin.ModelAdmin):
    pass
