from django.contrib import admin
from imports_exports.models import MappedImport

@admin.register(MappedImport)
class MappedImportAdmin(admin.ModelAdmin):
    pass
