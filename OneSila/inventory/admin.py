from django.contrib import admin
from core.admin import ModelAdmin

from inventory.models import Inventory


# Register your models here.

@admin.register(Inventory)
class InventoryAdmin(ModelAdmin):
    pass
