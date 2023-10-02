from django.db.models import Model

from strawberry import type, subscription
from strawberry.types import Info

from strawberry_django import NodeInput
from strawberry_django.permissions import get_with_perms
from strawberry_django.mutations.fields import get_pk

from typing import AsyncGenerator

import asyncio
from asgiref.sync import async_to_sync, sync_to_async

import channels.layers
from channels.db import database_sync_to_async

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
    group = get_group(instance)
    msg_type = get_msg_type(instance)
    msg = get_msg(instance)

    channel_layer = channels.layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)(group=group, message=msg)

    logger.debug(f"Send post_save message for '{instance}' to group '{group}' with msg: {msg}")


class ModelSubscribePublisher:
    """
    TODO:
    - Convert to use the entire strawberry_django structure and respect the extensions/filters
    - Write guide
    """

    def __init__(self, info: Info, input: NodeInput, model: Model):
        self.info = info
        self.input = input
        self.model = model

        self.ws = info.context["ws"]
        self.channel_layer = self.ws.channel_layer

    @database_sync_to_async
    def set_instance(self):
        vinput = vars(self.input).copy() if self.input is not None else {}
        pk = get_pk(vinput)
        instance = get_with_perms(pk, self.info, required=True, model=self.model)
        self.instance = instance

    @sync_to_async
    def refresh_instance(self):
        self.instance.refresh_from_db()
        return self.instance

    @property
    def group(self):
        return get_group(self.instance)

    @property
    def msg_type(self):
        return get_msg_type(self.instance)

    @property
    def msg(self):
        return get_msg(self.instance)

    async def subscribe(self):
        logger.debug(f"About to subscribe to group")
        resp = await self.channel_layer.group_add(self.group, self.ws.channel_name)
        logger.debug(f"Subscribed to group {self.group} with resp {resp}")

    async def send_message(self):
        logger.debug(f"About to send message")
        await self.channel_layer.group_send(group=self.group, message=self.msg)
        logger.debug(f"Sent message to group: {self.group} with message {self.msg}")

    async def send_initial_message(self):
        await self.send_message()

    async def publish_messages(self):
        async with self.ws.listen_to_channel(type=self.msg_type, groups=[self.group]) as messages:
            async for msg in messages:
                logger.info(f"Found message: {msg}")
                yield await self.refresh_instance()


async def model_subscribe_publisher(info: Info, input: NodeInput, model: Model) -> AsyncGenerator[type, None]:
    fac = ModelSubscribePublisher(info=info, input=input, model=model)
    await fac.set_instance()
    await fac.subscribe()
    await fac.send_initial_message()
    async for i in fac.publish_messages():
        yield i
