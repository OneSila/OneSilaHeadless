from media.flows import cleanup_media_storage_flow
from huey import crontab
from huey.contrib.djhuey import db_periodic_task
from huey.contrib.djhuey import db_task


@db_task()
def cleanup_media_storage_task(media_instance):
    cleanup_media_storage_flow(media_instance)
