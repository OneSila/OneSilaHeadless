from django.db.models.signals import post_save
from django.dispatch import receiver
from contacts.models import Company

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Company)
def send_company_message(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    import channels.layers
    from asgiref.sync import async_to_sync

    group = str(instance.__class__.__name__)
    msg_type = f"{group}_{instance.id}"
    msg = {'type': msg_type}

    channel_layer = channels.layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)(group=group, message=msg)
    logger.debug(f"Send post_save message for '{instance}' to group '{group}' with msg: {msg}")
