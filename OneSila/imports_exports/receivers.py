from django.dispatch import receiver
from core.signals import post_create
from imports_exports.models import MappedImport
from imports_exports.tasks import run_mapped_import_task


@receiver(post_create, sender=MappedImport)
def imports_exports__run_mapped_import_on_create(sender, instance, **kwargs):
    run_mapped_import_task(instance.id)