from quickbooks.objects import Address as QuickbookAddress
from contacts.models import Address


def map_qb_address(address: Address) -> QuickbookAddress:
    """
    Maps a local address object to a QuickBooks Address object.
    """
    qb_address = QuickbookAddress()
    qb_address.Line1 = address.address1
    qb_address.Line2 = address.address2
    qb_address.City = address.city
    qb_address.Country = address.get_country_display()
    qb_address.PostalCode = address.postcode
    return qb_address