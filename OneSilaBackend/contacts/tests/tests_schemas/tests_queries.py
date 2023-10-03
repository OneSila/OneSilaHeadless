from django.test import TestCase, TransactionTestCase
from model_bakery import baker

from OneSila.schema import schema
from contacts.models import Company, Supplier, Customer, Influencer, Person, Address, \
    ShippingAddress, InvoiceAddress

# FIXME: async test_ are not picked up by django testcase:
# https://stackoverflow.com/questions/49396918/django-ignoring-asynch-tests-completely-django-channels
# Alternativly, await django 5.0 upgrade in december 23:
# https://docs.djangoproject.com/en/5.0/topics/testing/tools/#transactiontestcase


class DeeplFactoryTestCase(TransactionTestCase):
    def setUp(self):
        self.companies = companies = baker.make(Company, _quantity=3)

    async def test_companies(self):
        query = """
            query companies {
                companies() {
                    id
                    name
                }
            }
        """

        # resp = await schema.execute(query, variable_values={"title": "The Great Gatsby"})
        resp = await schema.execute(query)
        assert result.errors is None
        # assert result.data["books"] == [
        #     {
        #         "title": "The Great Gatsby",
        #         "author": "F. Scott Fitzgerald",
        #     }
        # ]
