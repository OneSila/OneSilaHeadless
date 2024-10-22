import os


def get_invoice_pdf_upload_path(instance, filename):
    """
    Return a dynamic path for storing invoice PDFs based on the invoice ID.
    """
    path = os.path.join('invoices', str(instance.pk), 'invoice_pdfs', filename)
    return path

def get_credit_note_pdf_upload_path(instance, filename):
    """
    Return a dynamic path for storing credit note PDFs based on the credit note ID.
    """
    path = os.path.join('credit_notes', str(instance.pk), 'credit_note_pdfs', filename)
    return path