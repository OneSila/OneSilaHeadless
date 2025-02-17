from django.urls import reverse

from core.tests import TestCase, TestCaseDemoDataMixin
from core.helpers import save_test_file
from purchasing.models import PurchaseOrder

import logging
logger = logging.getLogger(__name__)


# class TestPrepareShipmentFactoryTestCase(TestCaseDemoDataMixin, TestCase):
#     def test_print_po_pdf(self):
#         po = PurchaseOrder.objects.filter(multi_tenant_company=self.multi_tenant_company).last()
#         filename, pdf = po.print()
#
#         filepath = save_test_file(filename, pdf)
#         logger.debug(f'Store test pdf here: {filepath}')
#
#         url = po.print_url()
#         resp = self.client.get(url)
#         self.assertEqual(resp.status_code, 200)
