from huey.contrib.djhuey import db_periodic_task
from huey.contrib.djhuey import db_task
from huey import crontab
from imports_exports.models import Export, MappedImport


@db_periodic_task(crontab(minute='3'))
def imports_exports__run_periodic_mapped_imports():
    """
    Periodically run all MappedImports that are due and marked as periodic.
    """
    to_run = MappedImport.objects.filter(is_periodic=True).exclude(status=MappedImport.STATUS_PROCESSING)

    for imp in to_run:
        if imp.should_run():
            imp.run(run_async=True)


@db_task()
def run_mapped_import_task(mapped_import_id):
    try:
        imp = MappedImport.objects.get(id=mapped_import_id)
        imp.run()
    except MappedImport.DoesNotExist:
        pass


@db_periodic_task(crontab(minute="7"))
def imports_exports__run_periodic_exports():
    to_run = Export.objects.filter(
        is_periodic=True,
        type=Export.TYPE_JSON_FEED,
    ).exclude(status=Export.STATUS_PROCESSING)

    for export in to_run:
        if export.should_run():
            export.run(run_async=True)


@db_task()
def run_export_task(*, export_id):
    try:
        export = Export.objects.get(id=export_id)
        export.run()
    except Export.DoesNotExist:
        pass
