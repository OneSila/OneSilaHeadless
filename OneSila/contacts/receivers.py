from django.db.models.signals import post_save
from django.dispatch import receiver
from contacts.models import Company, Supplier, Customer, Influencer, InternalCompany, \
    Person, Address, ShippingAddress, InvoiceAddress

import logging
logger = logging.getLogger(__name__)
