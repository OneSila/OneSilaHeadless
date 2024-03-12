# import pytest
# from model_bakery import baker
# from django.test import TestCase
# from OneSila.schema import schema  # Import your Strawberry schema
# from taxes.models import Tax
#
# class TaxSubscriptionTestCase(TestCase):
#     def setUp(self):
#         super().setUp()
#         self.tax = baker.make(Tax, rate='12', name='12%')
#     @pytest.mark.asyncio
#     async def test_tax_subscription(self):
#
#         # Define the subscription query
#         subscription_query = """
#             subscription taxSubscription($pk: String!) {
#                 tax(pk: $pk) {
#                     id
#                     rate
#                     name
#                 }
#             }
#         """
#
#         # Subscribe to the schema
#         sub = await schema.subscribe(subscription_query, variable_values={"pk": str(self.tax.pk)})
#
#         # Get the next result from the subscription
#         result = await sub.__anext__()
#
#         # Assert that there are no errors and the data is as expected
#         assert not result.errors
#         assert result.data["tax"]["id"] == str(self.tax.id)
#         assert result.data["tax"]["rate"] == self.tax.rate
#         assert result.data["tax"]["name"] == self.tax.name
#
