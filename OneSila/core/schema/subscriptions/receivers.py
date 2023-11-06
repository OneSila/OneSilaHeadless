from asgiref.sync import async_to_sync
from .helpers import get_group, get_msg
import channels.layers

import logging
logger = logging.getLogger(__name__)


def refresh_subscription_receiver(instance):
    group = get_group(instance)
    msg = get_msg(instance)

    channel_layer = channels.layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)(group=group, message=msg)

    logger.debug(f"Send post_save message {instance.__class__} for '{instance}' to group '{group}' with msg: {msg}")
