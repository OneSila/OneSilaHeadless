from django.contrib import admin
from core.admin import ModelAdmin
from contacts.models import Company, Person, Address


@admin.register(Company)
class CompanyAdmin(ModelAdmin):
    pass


@admin.register(Address)
class AddressAdmin(ModelAdmin):
    pass


@admin.register(Person)
class ContactAdmin(ModelAdmin):
    pass
