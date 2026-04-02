from django.urls import path

from imports_exports.views import DirectExportFeedView


urlpatterns = [
    path("<str:feed_key>/", DirectExportFeedView.as_view(), name="imports_exports_direct_export"),
]
