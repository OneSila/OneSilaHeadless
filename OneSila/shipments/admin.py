from django.contrib import admin

from shipments.models import Package


# Register your models here.

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    pass