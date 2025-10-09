from django.core.exceptions import ValidationError
from core.schema.core.mixins import GetCurrentUserMixin
from core.schema.core.mutations import Info, Any
from core.schema.core.mutations import UpdateMutation
from sales_channels.models import SalesChannelViewAssign, SalesChannel
from sales_channels.signals import manual_sync_remote_product, refresh_website_pull_models
from django.utils.translation import gettext_lazy as _


class ResyncSalesChannelAssignMutation(UpdateMutation, GetCurrentUserMixin):
    def update(self, info: Info, instance: SalesChannelViewAssign, data: dict[str, Any]):

        if instance.remote_product.syncing_current_percentage != 100:
            raise ValidationError(_("You can't resync the product because is currently syncing."))

        manual_sync_remote_product.send(
            sender=instance.remote_product.__class__,
            instance=instance.remote_product,
            view=instance.sales_channel_view,
        )

        return instance


class RefreshSalesChannelWebsiteModelsMutation(UpdateMutation, GetCurrentUserMixin):
    def update(self, info: Info, instance: SalesChannel, data: dict[str, Any]):
        if not instance.active:
            raise ValidationError(_("Sales channel is not active."))

        refresh_website_pull_models.send(sender=instance.__class__, instance=instance)

        return instance
