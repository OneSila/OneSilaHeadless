from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from core.schema.core.subscriptions import refresh_subscription_receiver
from django.utils.translation import gettext_lazy as _
from media.models import MediaProductThrough, Media, Image
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MediaProductThrough)
@receiver(post_delete, sender=MediaProductThrough)
def media__images__subscription__post_save(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    refresh_subscription_receiver(instance.product)


@receiver(pre_delete, sender=Media)
@receiver(pre_delete, sender=Image)
def prevent_media_delete_if_linked(sender, instance, **kwargs):
    from properties.models import PropertySelectValue

    if instance.products.exists():
        raise ValidationError(_("Cannot delete Media because it is used on a product."))

    if PropertySelectValue.objects.filter(image=instance).exists():
        raise ValidationError(_("Cannot delete Media because it is used in Property Select Values."))