from media.exceptions import NotSafeToRemoveError

import logging
logger = logging.getLogger(__name__)


def cleanup_media_storage_flow(media_instance):
    """
    This flow will clean up the image storage.
    """
    from media.factories.storage_cleanup import CleanupMediaStorageFactory

    try:
        f = CleanupMediaStorageFactory(media_instance)
        f.run()
    except NotSafeToRemoveError as e:
        logger.info(f"Media instance {media_instance.id} is not safe to remove. It is used by other media instances.")
