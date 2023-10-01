import strawberry_django

from strawberry import type, subscription
from strawberry.types import Info
from typing import List, AsyncGenerator

from asgiref.sync import sync_to_async
import asyncio

from strawberry_django.permissions import IsAuthenticated
from strawberry_django.relay import ListConnectionWithTotalCount

import logging
logger = logging.getLogger(__name__)


def get_group(instance):
    return f"{instance.__class__.__name__}"


def get_msg_type(instance):
    group = get_group(instance)
    return f"{group}_{instance.id}"


def get_msg(instance):
    return {'type': get_msg_type(instance)}


def refresh_subscription(instance):
    import channels.layers
    from asgiref.sync import async_to_sync

    group = get_group(instance)
    msg_type = get_msg_type(instance)
    msg = get_msg(instance)

    channel_layer = channels.layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)(group=group, message=msg)

    logger.debug(f"Send post_save message for '{instance}' to group '{group}' with msg: {msg}")
