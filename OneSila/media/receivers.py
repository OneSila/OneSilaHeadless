from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from core.models import MultiTenantCompany
from core.signals import post_create
from core.schema.core.subscriptions import refresh_subscription_receiver
from django.utils.translation import gettext_lazy as _
from media.models import MediaProductThrough, Media, Image, File, Video, DocumentType
import logging
from .signals import cleanup_media_storage

logger = logging.getLogger(__name__)


@receiver(post_create, sender=MultiTenantCompany)
def media__multi_tenant_company__create_internal_document_type(sender, instance, **kwargs):
    DocumentType.objects.create_internal_for_company(
        multi_tenant_company=instance,
    )


@receiver(post_save, sender=MediaProductThrough)
@receiver(post_delete, sender=MediaProductThrough)
def media__images__subscription__post_save(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    refresh_subscription_receiver(instance.product)


def _is_file_media_assignment(*, instance: MediaProductThrough) -> bool:
    if not getattr(instance, "media_id", None):
        return False

    return Media.objects.filter(
        id=instance.media_id,
        type=Media.FILE,
    ).exists()


def _get_configurable_variation_ids(*, instance: MediaProductThrough) -> list[int]:
    product = getattr(instance, "product", None)
    if product is None or not product.is_configurable():
        return []

    return list(
        product.get_configurable_variations(active_only=False).values_list("id", flat=True)
    )


@receiver(post_save, sender=MediaProductThrough)
def media__documents__configurable__propagate_to_children_on_create(sender, instance, created, **kwargs):
    if not created:
        return

    if not _is_file_media_assignment(instance=instance):
        return

    variation_ids = _get_configurable_variation_ids(instance=instance)
    if not variation_ids:
        return

    existing_product_ids = set(
        MediaProductThrough.objects.filter(
            product_id__in=variation_ids,
            media_id=instance.media_id,
            sales_channel=instance.sales_channel,
        ).values_list("product_id", flat=True)
    )

    new_assignments = [
        MediaProductThrough(
            multi_tenant_company_id=instance.multi_tenant_company_id,
            product_id=variation_id,
            media_id=instance.media_id,
            sort_order=instance.sort_order,
            sales_channel=instance.sales_channel,
        )
        for variation_id in variation_ids
        if variation_id not in existing_product_ids
    ]

    if not new_assignments:
        return

    MediaProductThrough.objects.bulk_create(
        new_assignments,
        ignore_conflicts=True,
    )


@receiver(post_delete, sender=MediaProductThrough)
def media__documents__configurable__remove_from_children_on_delete(sender, instance, **kwargs):
    if not _is_file_media_assignment(instance=instance):
        return

    variation_ids = _get_configurable_variation_ids(instance=instance)
    if not variation_ids:
        return

    MediaProductThrough.objects.filter(
        product_id__in=variation_ids,
        media_id=instance.media_id,
        sales_channel=instance.sales_channel,
    ).delete()


@receiver(pre_delete, sender=Media)
@receiver(pre_delete, sender=Image)
def prevent_media_delete_if_linked(sender, instance, **kwargs):
    from properties.models import PropertySelectValue

    if instance.products.exists():
        raise ValidationError(_("Cannot delete Media because it is used on a product."))

    if PropertySelectValue.objects.filter(image=instance).exists():
        raise ValidationError(_("Cannot delete Media because it is used in Property Select Values."))

@receiver(post_save, sender=Media)
@receiver(post_save, sender=Image)
@receiver(post_save, sender=File)
@receiver(post_save, sender=Video)
def populate_media_title_signal_sender(sender, instance, **kwargs):
    from .tasks import populate_media_title_task
    populate_media_title_task(instance)


@receiver(post_save, sender=Media)
@receiver(post_save, sender=File)
def process_document_media_assets_signal_sender(sender, instance, created, update_fields=None, **kwargs):
    if instance.type != Media.FILE:
        return

    if not created and update_fields is not None:
        if set(update_fields).isdisjoint({"file", "image", "is_document_image", "type", "document_image_thumbnail"}):
            return

    from .tasks import process_document_media_assets_task
    process_document_media_assets_task(media_id=instance.id)


@receiver(post_delete, sender=Image)
@receiver(post_delete, sender=Media)
def cleanup_image_storage_signal_sender(sender, instance, **kwargs):
    cleanup_media_storage.send(sender, instance=instance)


@receiver(cleanup_media_storage, sender=Image)
@receiver(cleanup_media_storage, sender=Media)
@receiver(cleanup_media_storage, sender=File)
@receiver(cleanup_media_storage, sender=Video)
def cleanup_image_storage_receiver(sender, instance, **kwargs):
    """ we trigger a task that will clean up the image which was removed from the database."""
    from .tasks import cleanup_media_storage_task
    cleanup_media_storage_task(instance)
