from django.contrib import admin

from inventory.models import Inventory


# Register your models here.

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    pass
