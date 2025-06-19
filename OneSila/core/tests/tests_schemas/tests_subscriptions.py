from contextlib import asynccontextmanager
from types import SimpleNamespace

from asgiref.sync import async_to_sync
from channels.layers import InMemoryChannelLayer
from model_bakery import baker

from core.tests import TransactionTestCase
from core.models import MultiTenantCompany, MultiTenantUser
from core.schema.core.subscriptions.publishers import ModelInstanceSubscribePublisher
from core.schema.core.subscriptions.helpers import create_global_id
from products.models import Product


class FakeWS:
    def __init__(self, channel_layer=None):
        self.channel_layer = channel_layer or InMemoryChannelLayer()
        self.channel_name = "test-channel"

    @asynccontextmanager
    async def listen_to_channel(self, type, *, timeout=None, groups=()):
        for group in groups:
            await self.channel_layer.group_add(group, self.channel_name)

        async def generator():
            while True:
                msg = await self.channel_layer.receive(self.channel_name)
                yield msg

        try:
            yield generator()
        finally:
            for group in groups:
                await self.channel_layer.group_discard(group, self.channel_name)


class ModelInstanceSubscribePublisherTests(TransactionTestCase):
    def test_group_removed_after_disconnect(self):
        channel_layer = InMemoryChannelLayer()
        ws = FakeWS(channel_layer=channel_layer)

        company = baker.make(MultiTenantCompany)
        user = baker.make(MultiTenantUser, multi_tenant_company=company)
        product = baker.make(Product, multi_tenant_company=company, type=Product.SIMPLE)

        info = SimpleNamespace(
            context={
                "ws": ws,
                "request": SimpleNamespace(user=user),
            },
            return_type=SimpleNamespace(__name__="ProductType"),
        )

        pk = create_global_id(product)
        publisher = ModelInstanceSubscribePublisher(
            info=info,
            pk=pk,
            model=Product,
        )

        async def run_pub():
            gen = publisher.await_messages()
            await gen.__anext__()
            self.assertIn(
                ws.channel_name,
                channel_layer.groups.get("Product", {}),
            )
            await gen.aclose()

        async_to_sync(run_pub)()

        self.assertNotIn("Product", channel_layer.groups)
