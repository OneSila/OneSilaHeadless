from django.db.models.signals import post_save
from django.dispatch import receiver
from contacts.models import Company, Supplier, Customer, Influencer, InternalCompany, \
    Person, Address, ShippingAddress, InvoiceAddress

from core.schema.core.subscriptions import refresh_subscription_receiver

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Company)
@receiver(post_save, sender=Supplier)
@receiver(post_save, sender=Customer)
@receiver(post_save, sender=Influencer)
@receiver(post_save, sender=InternalCompany)
@receiver(post_save, sender=Person)
@receiver(post_save, sender=Address)
@receiver(post_save, sender=ShippingAddress)
@receiver(post_save, sender=InvoiceAddress)
def contacts__subscription__post_save(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    refresh_subscription_receiver(instance)
