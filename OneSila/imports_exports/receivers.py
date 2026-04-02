from django.dispatch import receiver
from core.signals import post_create, post_update
from imports_exports.models import Export, Import, MappedImport
@receiver(post_create, sender=MappedImport)
def imports_exports__run_mapped_import_on_create(sender, instance, **kwargs):
    if instance.status == Import.STATUS_PENDING:
        instance.run(run_async=True)


@receiver(post_update, sender=MappedImport)
def imports_exports__retry_mapped_import_on_pending(sender, instance, **kwargs):

    if instance.status == Import.STATUS_PENDING:
        instance.run(run_async=True)


@receiver(post_create, sender=Export)
def imports_exports__run_export_on_create(sender, instance, **kwargs):
    if instance.status == Export.STATUS_PENDING:
        instance.run(run_async=True)


@receiver(post_update, sender=Export)
def imports_exports__retry_export_on_pending(sender, instance, **kwargs):
    if instance.status == Export.STATUS_PENDING:
        instance.run(run_async=True)
