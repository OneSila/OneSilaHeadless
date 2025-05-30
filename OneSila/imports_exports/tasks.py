from huey.contrib.djhuey import db_periodic_task
from huey.contrib.djhuey import db_task
from huey import crontab
from imports_exports.models import MappedImport


@db_periodic_task(crontab(minute='3'))
def imports_exports__run_periodic_mapped_imports():
    """
    Periodically run all MappedImports that are due and marked as periodic.
    """
    to_run = MappedImport.objects.filter(is_periodic=True)

    for imp in to_run:
        if imp.should_run():
            imp.run()


@db_task()
def run_mapped_import_task(mapped_import_id):
    try:
        imp = MappedImport.objects.get(id=mapped_import_id)
        imp.run()
    except MappedImport.DoesNotExist:
        pass