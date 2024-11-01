from django.contrib import admin

from accounting.integrations.quickbooks.models import QuickbooksAccount, QuickbooksVat, QuickbooksInvoice, QuickbooksCustomer, QuickbooksCreditNote


@admin.register(QuickbooksAccount)
class QuickbooksAccountAdmin(admin.ModelAdmin):
    pass

@admin.register(QuickbooksVat)
class QuickbooksVatAdmin(admin.ModelAdmin):
    pass

@admin.register(QuickbooksInvoice)
class QuickbooksInvoiceAdmin(admin.ModelAdmin):
    pass

@admin.register(QuickbooksCustomer)
class QuickbooksCustomerAdmin(admin.ModelAdmin):
    pass

@admin.register(QuickbooksCreditNote)
class QuickbooksCreditNoteAdmin(admin.ModelAdmin):
    pass