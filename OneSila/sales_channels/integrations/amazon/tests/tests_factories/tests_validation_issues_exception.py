from core.tests import TestCase
from products.models import Product
from model_bakery import baker

from sales_channels.integrations.amazon.exceptions import AmazonProductValidationIssuesException
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.models import (
    AmazonProduct,
    AmazonProductIssue,
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

    def test_update_assign_issues_raises_user_exception_and_persists_validation_issues(self):
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

        with self.assertRaises(AmazonProductValidationIssuesException):
            fac.update_assign_issues(issues)

        self.assertTrue(
            AmazonProductIssue.objects.filter(
                remote_product=self.remote_product,
                view=self.view,
                is_validation_issue=True,
            ).exists()
        )

    def test_exception_is_registered_as_user_exception(self):
        self.assertIn(AmazonProductValidationIssuesException, self.sales_channel._meta.user_exceptions)
