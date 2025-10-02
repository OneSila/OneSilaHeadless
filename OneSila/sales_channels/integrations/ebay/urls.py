from django.urls import path

from . import views

app_name = "ebay"

urlpatterns = [
    path(
        "account-deletion/",
        views.ebay_marketplace_account_deletion,
        name="marketplace_account_deletion",
    ),
]
