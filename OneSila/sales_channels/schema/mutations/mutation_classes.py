from django.core.exceptions import ValidationError
from core.schema.core.mixins import GetCurrentUserMixin
from core.schema.core.mutations import Info, Any
from core.schema.core.mutations import UpdateMutation
from sales_channels.models import SalesChannelViewAssign
from sales_channels.signals import sync_remote_product
from django.utils.translation import gettext_lazy as _


class ResyncSalesChannelAssignMutation(UpdateMutation, GetCurrentUserMixin):
    def update(self, info: Info, instance: SalesChannelViewAssign, data: dict[str, Any]):

        if instance.remote_product.syncing_current_percentage != 100:
            raise ValidationError(_("You can't resync the product because is currently syncing."))


        sync_remote_product.send(sender=instance.remote_product.__class__, instance=instance.remote_product)
        print('----------------------------')
        print(instance.remote_product.__class__)


        return instance
