from strawberry_django import NodeInput
from django.db.models import Model
from core.schema.subscriptions import type, subscription, Info, AsyncGenerator, asyncio, List
from core.schema.subscriptions import get_msg, get_group, get_msg_type
from core.schema.queries import node

from asgiref.sync import async_to_sync, sync_to_async

from strawberry_django.permissions import filter_with_perms, get_with_perms
from strawberry_django.auth.utils import get_current_user
from strawberry_django.mutations.fields import get_pk
from strawberry_django.subscriptions.fields import subscription_node
from strawberry.relay.utils import from_base64
from channels.db import database_sync_to_async

from core.decorators import timeit_and_log

from contacts.models import Company
from .types.input import CompanyPartialInput
from .types.types import CompanyType

from typing import cast, Dict
import json

import json

import logging
logger = logging.getLogger(__name__)


class ModelSubscribePublisher:
    def __init__(self, info: Info, input: NodeInput, model: Model):
        self.info = info
        self.input = input
        self.model = model

        self.ws = info.context["ws"]
        self.channel_layer = self.ws.channel_layer

    @timeit_and_log(logger)
    @database_sync_to_async
    def set_instance(self):
        vinput = vars(self.input).copy() if self.input is not None else {}
        pk = get_pk(vinput)
        instance = get_with_perms(pk, self.info, required=True, model=self.model)
        self.instance = instance

    @timeit_and_log(logger)
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

    @timeit_and_log(logger)
    async def subscribe(self):
        logger.debug(f"About to subscribe to group")
        resp = await self.channel_layer.group_add(self.group, self.ws.channel_name)
        logger.debug(f"Subscribed to group {self.group} with resp {resp}")

    @timeit_and_log(logger)
    async def send_message(self):
        logger.debug(f"About to send message")
        await self.channel_layer.group_send(group=self.group, message=self.msg)
        logger.debug(f"Sent message to group: {self.group} with message {self.msg}")

    @timeit_and_log(logger)
    async def send_initial_message(self):
        await self.send_message()

    @timeit_and_log(logger)
    async def publish_messages(self):
        async with self.ws.listen_to_channel(type=self.msg_type, groups=[self.group]) as messages:
            async for msg in messages:
                logger.info(f"Found message: {msg}")
                yield await self.refresh_instance()


@type(name="Subscription")
class ContactsSubscription:
    company_node: CompanyType = node(is_subscription=True)
    # company_subscription_node: CompanyType = await subscription_node()

    # @subscription
    # async def company(self, info: Info, data: CompanyPartialInput) -> AsyncGenerator[CompanyType, None]:
    #     """
    #     TODO:
    #     - Convert to use the entire strawberry_django structure and respect the extensions/filters
    #     - Abstractize, to ensure it's re-usable for the other models
    #     - Write guide
    #     """

    #     @database_sync_to_async
    #     def get_instance(*, pk, info, model):
    #         return get_with_perms(pk, info, required=True, model=model)

    #     # What model will we be fetching/serving?
    #     model = Company

    #     # Prepare the channel information and base intance to monitor
    #     ws = info.context["ws"]
    #     channel_layer = ws.channel_layer
    #     vinput = vars(data).copy() if data is not None else {}
    #     pk = get_pk(vinput)
    #     # instance = await database_sync_to_async(lambda: get_with_perms(pk, info, required=True, model=model))()

    #     logger.debug(f"Done prepping channel and input-data")

    #     # Perpare your message structure and send the welcome message.
    #     instance = await get_instance(pk=pk, info=info, model=model)
    #     group = get_group(instance)
    #     msg = get_msg(instance)
    #     msg_type = get_msg_type(instance)

    #     await channel_layer.group_add(group, ws.channel_name)
    #     await channel_layer.group_send(group=group, message=msg)

    #     logger.debug(f"Done subscribing and sending initial data to group '{group}' with message '{msg}")

    #     # This is where the magic happens.  Monitor your group for relvant messages to
    #     # this subscription and serve your instance.
    #     async with ws.listen_to_channel(type=msg_type, groups=[group]) as messages:
    #         async for msg in messages:
    #             logger.info(f"Found message: {msg}, yielding fresh instance")
    #             yield await get_instance(pk=pk, info=info, model=model)

    @subscription
    async def company_class(self, info: Info, data: CompanyPartialInput) -> AsyncGenerator[CompanyType, None]:
        fac = ModelSubscribePublisher(info=info, input=data, model=Company)
        await fac.set_instance()
        await fac.subscribe()
        await fac.send_initial_message()
        async for i in fac.publish_messages():
            print(i.name)
            yield i

    # @subscription
    # async def my_company(self, data: CompanyPartialInput) -> CompanyType:
    #     # https://www.valentinog.com/blog/channels-ariadne/
    #     while True:
    #         await asyncio.sleep(1)
    #         yield await database_sync_to_async(lambda: get_instance(data=data, info=self.info))()
