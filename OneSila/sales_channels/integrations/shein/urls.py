from django.urls import path

from sales_channels.integrations.shein import views


app_name = "shein"

urlpatterns = [
    path(
        "webhooks",
        views.shein_product_document_audit_status_notice,
        name="product_document_audit_status_notice",
    ),
]

