from media.flows import cleanup_media_storage_flow, populate_title_flow
from huey import crontab
from huey.contrib.djhuey import db_periodic_task
from huey.contrib.djhuey import db_task


@db_task()
def cleanup_media_storage_task(media_instance):
    cleanup_media_storage_flow(media_instance)


@db_task()
def populate_media_title_task(media_instance):
    """
    Background task to populate media title from filename.
    """
    populate_title_flow(media_instance)
