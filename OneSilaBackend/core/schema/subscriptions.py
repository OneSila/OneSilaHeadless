from django.db.models import Model

from functools import wraps, partial

from strawberry import type, subscription
from strawberry.types import Info
from strawberry.relay.types import GlobalID
from strawberry.relay.utils import from_base64

from strawberry_django import NodeInput
from strawberry_django.auth.utils import get_current_user
from strawberry_django.mutations.fields import get_pk

from typing import AsyncGenerator, Any

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
    msg = get_msg(instance)

    channel_layer = channels.layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)(group=group, message=msg)

    logger.debug(f"Send post_save message {instance.__class__} for '{instance}' to group '{group}' with msg: {msg}")


class ModelSubscribePublisher:
    """
    TODO:
    - Convert to use the entire strawberry_django structure and respect the extensions/filters
    - Write guide
    """

    def __init__(self, info: Info, pk: GlobalID, model: Model):
        self.info = info
        self.pk = pk
        self.model = model

        self.ws = info.context["ws"]
        self.channel_layer = self.ws.channel_layer

    def get_queryset(self):
        user = get_current_user(self.info)
        multi_tenant_company = user.multi_tenant_company
        return self.model.objects.filter(multi_tenant_company=multi_tenant_company)

    @database_sync_to_async
    def set_instance(self):
        _, pk = from_base64(self.pk)
        instance = self.get_queryset().get(pk=pk)
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
        resp = await self.channel_layer.group_add(self.group, self.ws.channel_name)
        logger.debug(f"Subscribed to group {self.group} with resp {resp}")

    async def send_message(self):
        await self.channel_layer.group_send(group=self.group, message=self.msg)
        logger.debug(f"Sent message {self.msg} to group {self.group}")

    async def send_initial_message(self):
        await self.send_message()

    async def publish_messages(self):
        async with self.ws.listen_to_channel(type=self.msg_type, groups=[self.group]) as messages:
            async for msg in messages:
                logger.info(f"Found wakup: {msg}")
                yield await self.refresh_instance()


async def model_subscribe_publisher(info: Info, pk: GlobalID, model: Model) -> AsyncGenerator[Any, None]:
    fac = ModelSubscribePublisher(info=info, pk=pk, model=model)
    await fac.set_instance()
    await fac.subscribe()
    await fac.send_initial_message()
    async for i in fac.publish_messages():
        yield i


def model_subscription_field(model):
    # FIMXE: Using this wrapper with @subscription breaks somewhwere inside of the subscription decorator.
    # using it without @subscription return None instead of the AsyncGenerator.
    @subscription
    async def model_subscription_inner(info: Info, pk: GlobalID, model: Model) -> AsyncGenerator[Any, None]:
        async for i in model_subscribe_publisher(info=info, pk=pk, model=model):
            yield i
    return model_subscription_inner
