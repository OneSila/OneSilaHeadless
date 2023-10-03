import pytest
from model_bakery import baker

from OneSila.schema import schema
from contacts.models import Company, Supplier, Customer, Influencer, Person, Address, \
    ShippingAddress, InvoiceAddress


@pytest.mark.asyncio
async def test_companies():
    companies = baker.make(Company, _quantity=3)

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
