from core.schema.subscriptions import type, subscription, Info, AsyncGenerator, model_subscribe_publisher

from contacts.models import Company
from .types.input import CompanyPartialInput
from .types.types import CompanyType


@type(name="Subscription")
class ContactsSubscription:
    @subscription
    async def company_class(self, info: Info, data: CompanyPartialInput) -> AsyncGenerator[CompanyType, None]:
        async for i in model_subscribe_publisher(info=info, input=data, model=Company):
            yield i

    # @subscription
    # async def company(self, info: Info, data: CompanyPartialInput) -> AsyncGenerator[CompanyType, None]:
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

    # @subscription
    # async def my_company(self, data: CompanyPartialInput) -> CompanyType:
    #     # https://www.valentinog.com/blog/channels-ariadne/
    #     while True:
    #         await asyncio.sleep(1)
    #         yield await database_sync_to_async(lambda: get_instance(data=data, info=self.info))()
