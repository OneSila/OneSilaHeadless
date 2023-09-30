from core.schema.subscriptions import type, subscription, Info, AsyncGenerator, asyncio, List
from core.schema.queries import node

from strawberry_django.permissions import filter_with_perms, get_with_perms
from strawberry_django.auth.queries import get_current_user
from strawberry_django.mutations.fields import get_pk
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
    def __init__(self, info: Info, input: CompanyPartialInput, model: Company):
        self.info = info
        self.input = input
        self.model = model

        self.ws = info.context["ws"]
        self.channel_layer = self.ws.channel_layer

    @database_sync_to_async
    def get_instance(self):
        vinput = vars(self.input).copy() if self.input is not None else {}
        pk = get_pk(vinput)

        instance = get_with_perms(pk, self.info, required=True, model=self.model)
        return instance

    async def get_group(self):
        instance = await self.get_instance()
        return str(instance.__class__.__name__)

    async def get_msg_type(self):
        group = await self.get_group()
        instance = await self.get_instance()
        return f"{group}_{instance.id}"

    @timeit_and_log(logger)
    async def subscribe(self):
        group = await self.get_group()
        await self.channel_layer.group_add(group, self.ws.channel_name)

    @timeit_and_log(logger)
    async def send_message(self):
        logger.debug(f"About to send message")

        msg_type = await self.get_msg_type()
        group = await self.get_group()
        msg = {'type': msg_type}
        await self.channel_layer.group_send(group=group, message=msg)
        # # async_to_sync(self.channel_layer.group_send)(group=group, message=message)
        logger.debug(f"Sent message to group: {group} with message {msg}")

    @timeit_and_log(logger)
    async def send_initial_message(self):
        await self.send_message()

    @timeit_and_log(logger)
    async def publish_messages(self):
        msg_type = await self.get_msg_type()
        group = await self.get_group()

        async with self.ws.listen_to_channel(type=msg_type, groups=[group]) as messages:
            async for msg in messages:
                logger.info(f"Found message: {msg}")
                yield self.get_instance()


@type(name="Subscription")
class ContactsSubscription:
    company_node: CompanyType = node()

    @subscription
    async def company(self, info: Info, data: CompanyPartialInput) -> AsyncGenerator[CompanyType, None]:
        """
        TODO:
        - Convert to use the entire strawberry_django structure and respect the extensions/filters
        - Abstractize, to ensure it's re-usable for the other models
        - Write guide
        """

        @database_sync_to_async
        def get_instance(*, pk, info, model):
            return get_with_perms(pk, info, required=True, model=model)

        # What model will we be fetching/serving?
        model = Company

        # Prepart the channel information and base intance to monitor
        ws = info.context["ws"]
        channel_layer = ws.channel_layer
        vinput = vars(data).copy() if data is not None else {}
        pk = get_pk(vinput)
        # instance = await database_sync_to_async(lambda: get_with_perms(pk, info, required=True, model=model))()

        logger.debug(f"Done prepping channel and input-data")

        # Perpare your message structure and send the welcome message.
        instance = await get_instance(pk=pk, info=info, model=model)
        group = f"{instance.__class__.__name__}"
        msg_type = f"{group}_{instance.id}"
        msg = {'type': msg_type}

        await channel_layer.group_add(group, ws.channel_name)
        await channel_layer.group_send(group=group, message=msg)

        logger.debug(f"Done subscribing and sending initial data to group '{group}' with message '{msg}")

        # This is where the magic happens.  Monitor your group for relvant messages to
        # this subscription and serve your instance.
        async with ws.listen_to_channel(type=msg_type, groups=[group]) as messages:
            async for msg in messages:
                logger.info(f"Found message: {msg}, yielding fresh instance")
                yield await get_instance(pk=pk, info=info, model=model)

        # fac = ModelSubscribePublisher(info=info, input=data, model=Company)
        # await fac.subscribe()
        # await fac.send_initial_message()
        # async for i in fac.publish_messages():
        #     yield await i

    @subscription
    async def my_company(self, data: CompanyPartialInput) -> CompanyType:
        # https://www.valentinog.com/blog/channels-ariadne/
        while True:
            await asyncio.sleep(1)
            yield await database_sync_to_async(lambda: get_instance(data=data, info=self.info))()
