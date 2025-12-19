from core.tests import TestCase
from products.models import Product
from model_bakery import baker
from unittest.mock import patch

from sales_channels.integrations.amazon.exceptions import AmazonProductValidationIssuesException
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.models import (
    AmazonProduct,
    AmazonSalesChannel,
    AmazonSalesChannelView,
)

from ..helpers import DisableWooCommerceSignalsMixin


class DummyFactory(GetAmazonAPIMixin):
    def __init__(self, *, sales_channel, remote_product, view):
        self.sales_channel = sales_channel
        self.remote_product = remote_product
        self.view = view

    def _get_client(self):
        return None


class AmazonValidationIssuesExceptionTest(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="VIEW",
        )
        local_product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=local_product,
        )

    @patch("sales_channels.integrations.amazon.factories.sales_channels.issues.FetchRemoteValidationIssueFactory.run")
    @patch("sales_channels.integrations.amazon.models.products.AmazonProduct.get_issues")
    def test_update_assign_issues_raises_user_exception_and_persists_validation_issues(self, get_issues, run_factory):
        fac = DummyFactory(
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            view=self.view,
        )

        issues = [
            {
                "code": "MISSING_ATTR",
                "message": "Missing required attribute: color",
                "severity": "ERROR",
            }
        ]

        get_issues.return_value = issues

        with self.assertRaises(AmazonProductValidationIssuesException):
            fac.update_assign_issues(issues)

        run_factory.assert_called_once()

    @patch("sales_channels.integrations.amazon.factories.sales_channels.issues.FetchRemoteValidationIssueFactory.run")
    @patch("sales_channels.integrations.amazon.models.products.AmazonProduct.get_issues")
    def test_update_assign_issues_does_not_raise_for_only_warning_severity(self, get_issues, run_factory):
        fac = DummyFactory(
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            view=self.view,
        )

        issues = [
            {
                "code": "RECOMMENDED_ATTR",
                "message": "Recommended attribute missing: color",
                "severity": "WARNING",
            }
        ]

        get_issues.return_value = issues

        fac.update_assign_issues(issues)

        run_factory.assert_called_once()

    def test_exception_is_registered_as_user_exception(self):
        self.assertIn(AmazonProductValidationIssuesException, self.sales_channel._meta.user_exceptions)
