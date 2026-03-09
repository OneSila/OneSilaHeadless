from media.flows import cleanup_media_storage_flow, populate_title_flow, generate_document_assets_flow
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


@db_task()
def process_document_media_assets_task(*, media_id):
    from media.models import Media

    try:
        media_instance = Media.objects.get(id=media_id)
    except Media.DoesNotExist:
        return

    generate_document_assets_flow(media_instance=media_instance)
