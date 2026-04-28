from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.urls import reverse
from django.test import RequestFactory, TransactionTestCase

from integrations.admin import PublicIntegrationTypeAdmin, PublicIssueRequestAdmin
from integrations.models import PublicIntegrationType, PublicIssueRequest
from integrations.tests.helpers import PublicIntegrationTypeSchemaMixin, PublicIssueSchemaMixin


class PublicIntegrationTypeAdminTests(PublicIntegrationTypeSchemaMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.admin = PublicIntegrationTypeAdmin(PublicIntegrationType, AdminSite())
        self.request = RequestFactory().post("/admin/integrations/publicintegrationtype/")

    @patch.object(PublicIntegrationTypeAdmin, "message_user")
    def test_enable_selected_marks_queryset_as_active(self, message_user_mock):
        first_integration_type = PublicIntegrationType.objects.create(
            key="admin-enable-first",
            type="channel",
            category=PublicIntegrationType.CATEGORY_STOREFRONT,
            active=False,
        )
        second_integration_type = PublicIntegrationType.objects.create(
            key="admin-enable-second",
            type="channel",
            category=PublicIntegrationType.CATEGORY_MARKETPLACE,
            active=False,
        )

        queryset = PublicIntegrationType.objects.filter(
            id__in=[first_integration_type.id, second_integration_type.id]
        )

        self.admin.enable_selected(self.request, queryset)

        self.assertFalse(queryset.filter(active=False).exists())
        message_user_mock.assert_called_once()

    @patch.object(PublicIntegrationTypeAdmin, "message_user")
    def test_disable_selected_marks_queryset_as_inactive(self, message_user_mock):
        first_integration_type = PublicIntegrationType.objects.create(
            key="admin-disable-first",
            type="channel",
            category=PublicIntegrationType.CATEGORY_STOREFRONT,
            active=True,
        )
        second_integration_type = PublicIntegrationType.objects.create(
            key="admin-disable-second",
            type="channel",
            category=PublicIntegrationType.CATEGORY_MARKETPLACE,
            active=True,
        )

        queryset = PublicIntegrationType.objects.filter(
            id__in=[first_integration_type.id, second_integration_type.id]
        )

        self.admin.disable_selected(self.request, queryset)

        self.assertFalse(queryset.filter(active=True).exists())
        message_user_mock.assert_called_once()


class PublicIssueRequestAdminTests(PublicIssueSchemaMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.admin = PublicIssueRequestAdmin(PublicIssueRequest, AdminSite())
