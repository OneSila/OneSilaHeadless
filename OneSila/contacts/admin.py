from django.contrib import admin
from contacts.models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    pass
