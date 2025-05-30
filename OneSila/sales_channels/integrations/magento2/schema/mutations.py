from sales_channels.integrations.magento2.factories.sales_channels.sales_channel import TryConnection
from sales_channels.integrations.magento2.schema.types.input import MagentoSalesChannelInput, \
    MagentoSalesChannelPartialInput, MagentoRemoteEanCodeAttributeInput
from sales_channels.integrations.magento2.schema.types.types import MagentoSalesChannelType, MagentoRemoteAttributeType
from core.schema.core.mutations import create, type, List, update
import strawberry_django
from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_multi_tenant_company
from strawberry import Info


@type(name="Mutation")
class MagentoSalesChannelMutation:
    create_magento_sales_channel: MagentoSalesChannelType = create(MagentoSalesChannelInput)
    create_magento_sales_channels: List[MagentoSalesChannelType] = create(MagentoSalesChannelInput)

    update_magento_sales_channel: MagentoSalesChannelType = update(MagentoSalesChannelPartialInput)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def create_remote_ean_code_attribute(self, instance: MagentoRemoteEanCodeAttributeInput, info: Info) -> MagentoRemoteAttributeType:
        from sales_channels.integrations.magento2.models.sales_channels import MagentoSalesChannel
        from magento.models import ProductAttribute
        import json

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        sales_channel = MagentoSalesChannel.objects.get(id=instance.sales_channel.id.node_id, multi_tenant_company=multi_tenant_company)
        api = TryConnection(sales_channel=sales_channel).api
        attribute = api.product_attributes.create(
            data={
                "attribute_code": instance.attribute_code,
                "frontend_input": ProductAttribute.TEXT,
                "default_frontend_label": instance.name
            }
        )

        return MagentoRemoteAttributeType(
            id=attribute.attribute_id,
            attribute_code=attribute.attribute_code,
            name=attribute.default_frontend_label,
            data=json.dumps(attribute.data)
        )
