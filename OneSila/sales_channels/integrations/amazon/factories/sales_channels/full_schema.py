from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin, PullAmazonMixin
from sales_channels.integrations.amazon.models.properties import AmazonProductType


class AmazonFullSchemaPullFactory(GetAmazonAPIMixin, PullAmazonMixin, PullRemoteInstanceMixin):
    """
    Pull factory to synchronize Amazon product types, items, properties, and select values.
    Main model: AmazonProductType, using category_code from get_product_types.
    """

    remote_model_class = AmazonProductType
    field_mapping = {
        'category_code': 'product_type',
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ['category_code', 'sales_channel']

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def fetch_remote_instances(self):
        """
        Fetch product types from Amazon's SP-API using get_product_types.
        """
        product_types = self.get_product_types()
        self.remote_instances = [
            {
                'product_type': pt,
            }
            for pt in product_types
        ]



    def post_pull_action(self):

        for pt in self.remote_instances:
            test = self.get_product_type_definition(pt['product_type'])
            print(test)
            break

    def pull_product_type_attributes(self, product_type):
        """
        Fetch attributes for a given product type and create AmazonProductTypeItem and AmazonProperty instances.
        """
        pass
