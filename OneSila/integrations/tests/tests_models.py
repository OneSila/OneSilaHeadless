from unittest.mock import patch

from django.test import TransactionTestCase

from integrations.models import (
    PublicIntegrationType,
    PublicIntegrationTypeTranslation,
    PublicIssue,
    PublicIssueImage,
    PublicIssueRequest,
)
from integrations.tests.helpers import PublicIntegrationTypeSchemaMixin, PublicIssueSchemaMixin


class PublicIntegrationTypeModelTests(PublicIntegrationTypeSchemaMixin, TransactionTestCase):
    def test_name_and_description_use_requested_language_and_fallback(self):
        integration_type = PublicIntegrationType.objects.create(
            key="amazon_model_test",
            type="channel",
            subtype="marketplace",
            category=PublicIntegrationType.CATEGORY_MARKETPLACE,
            active=True,
            is_beta=False,
            supports_open_ai_product_feed=True,
            sort_order=10,
        )
        PublicIntegrationTypeTranslation.objects.create(
            public_integration_type=integration_type,
            language="en",
            name="Amazon",
            description="English description",
        )
        PublicIntegrationTypeTranslation.objects.create(
            public_integration_type=integration_type,
            language="de",
            name="Amazon DE",
            description="",
        )

        self.assertEqual(integration_type.name(language="de"), "Amazon DE")
        self.assertEqual(integration_type.description(language="de"), "English description")
        self.assertEqual(integration_type.name(language="fr"), "Amazon DE")
        self.assertEqual(integration_type.description(language="fr"), "English description")

    def test_str_falls_back_to_key_when_no_translation_exists(self):
        integration_type = PublicIntegrationType.objects.create(
            key="shopify_model_test",
            type="channel",
            category=PublicIntegrationType.CATEGORY_STOREFRONT,
        )

        self.assertEqual(str(integration_type), "shopify_model_test")


class PublicIssueModelTests(PublicIssueSchemaMixin, TransactionTestCase):
    def test_generates_unique_four_digit_code_when_missing(self):
        integration_type = PublicIntegrationType.objects.create(
            key="ebay_public_issue_model_test",
            type="ebay",
            category=PublicIntegrationType.CATEGORY_MARKETPLACE,
        )

        first_issue = PublicIssue.objects.create(
            integration_type=integration_type,
            issue="The platform rejected the listing.",
            cause="The package weight is missing.",
            recommended_fix="Add package dimensions and retry sync.",
        )
        second_issue = PublicIssue.objects.create(
            integration_type=integration_type,
            issue="The platform rejected the variation.",
        )

        self.assertEqual(first_issue.code, "0001")
        self.assertEqual(second_issue.code, "0002")

    @patch("integrations.models.generate_absolute_url", return_value="https://app.example.com")
    def test_public_issue_image_get_image_url_returns_absolute_url(self, generate_absolute_url_mock):
        image = PublicIssueImage(image="public_issue_images/example.jpg")

        self.assertEqual(
            image.get_image_url(),
            f"https://app.example.com{image.image.url}",
        )
        generate_absolute_url_mock.assert_called_once_with(trailing_slash=False)


class PublicIssueRequestReceiverTests(PublicIssueSchemaMixin, TransactionTestCase):
    def test_post_create_signal_triggers_telegram_admin_notification_factory(self):
        integration_type = PublicIntegrationType.objects.create(
            key="ebay_public_issue_request_receiver_test",
            type="ebay",
            category=PublicIntegrationType.CATEGORY_MARKETPLACE,
        )

        with patch("integrations.receivers.TelegramAdminNotificationFactory") as factory_mock:
            request = PublicIssueRequest.objects.create(
                integration_type=integration_type,
                issue="The integration log says SKU TEST-1 failed validation.",
                description="It happened while syncing an Ebay listing.",
                submission_id="SUBMISSION-1",
                product_sku="TEST-1",
            )

        factory_mock.assert_called_once_with(public_issue_request=request)
        factory_mock.return_value.run.assert_called_once_with()

    def test_public_issue_with_request_reference_marks_request_accepted(self):
        integration_type = PublicIntegrationType.objects.create(
            key="ebay_public_issue_request_acceptance_test",
            type="ebay",
            category=PublicIntegrationType.CATEGORY_MARKETPLACE,
        )
        request = PublicIssueRequest.objects.create(
            integration_type=integration_type,
            issue="The integration log says SKU TEST-1 failed validation.",
        )

        PublicIssue.objects.create(
            integration_type=integration_type,
            issue="The integration log says SKU TEST-1 failed validation.",
            request_reference=request.id,
        )

        request.refresh_from_db()
        self.assertEqual(request.status, PublicIssueRequest.ACCEPTED)
