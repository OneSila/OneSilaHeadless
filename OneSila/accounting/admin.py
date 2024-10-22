from django.contrib import admin

from accounting.models import Invoice, CreditNote


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    pass

@admin.register(CreditNote)
class CreditNoteAdmin(admin.ModelAdmin):
    pass