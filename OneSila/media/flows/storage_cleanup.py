def cleanup_media_storage_flow(media_instance):
    """
    This flow will clean up the image storage.
    """
    from media.factories.storage_cleanup import CleanupMediaStorageFactory

    f = CleanupMediaStorageFactory(media_instance)
    f.run()
