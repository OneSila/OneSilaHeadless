from django.dispatch import receiver
from core.signals import post_create, post_update
from imports_exports.models import MappedImport, Import
from imports_exports.tasks import run_mapped_import_task


@receiver(post_create, sender=MappedImport)
def imports_exports__run_mapped_import_on_create(sender, instance, **kwargs):
    run_mapped_import_task(instance.id)


@receiver(post_update, sender=MappedImport)
def imports_exports__retry_mapped_import_on_pending(sender, instance, **kwargs):

    if instance.status == Import.STATUS_PENDING:
        run_mapped_import_task(instance.id)