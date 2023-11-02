from django.contrib import admin
from contacts.models import Company, Person, Address


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    pass


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    pass


@admin.register(Person)
class ContactAdmin(admin.ModelAdmin):
    pass
