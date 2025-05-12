from django.urls import path, include
from . import views
from .views import IntegrationListView

app_name = 'integrations'

urlpatterns = [
    path("", IntegrationListView.as_view(), name="integrations_list"),
]

