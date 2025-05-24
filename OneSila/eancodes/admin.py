from django.contrib import admin
from core.admin import ModelAdmin
from eancodes.models import EanCode


@admin.register(EanCode)
class EanCodeAdmin(ModelAdmin):
    pass
