from media.models import Media
from core.exceptions import ValidationError
import os
from media.exceptions import FailedToCleanupMediaStorage

import logging
logger = logging.getLogger(__name__)


class CleanupMediaStorageFactory:
    """
    Cleanup the image and cached image for a delted media instance.
    No need to handle Image instance. They Image model is a proxy to the Media model.
    """
    NATIVE_DJANGO_FIELD_TYPES = ['image', 'file']
    IMAGEKIT_FIELD_TYPES = ['onesila_thumbnail', 'image_web']

    def __init__(self, media_instance):
        self.media_instance = media_instance
        self.media_instance_id = media_instance.id

    def set_paths(self):
        """
        This method will set the image path.
        """
        for field in self.NATIVE_DJANGO_FIELD_TYPES:
            try:
                value = getattr(self.media_instance, field).path
                setattr(self, f"{field}_path", value)
                logger.debug(f"{field} field found for media instance {self.media_instance_id} at {value}")
            except (ValueError, AttributeError):
                setattr(self, f"{field}_path", None)
                logger.debug(f"{field} field not found for media instance {self.media_instance_id}.")

        for field in self.IMAGEKIT_FIELD_TYPES:
            try:
                value = getattr(self.media_instance, field).path
                setattr(self, f"{field}_path", value)
                logger.debug(f"{field} field found for media instance {self.media_instance_id} at {value}")
            except (ValueError, AttributeError):
                setattr(self, f"{field}_path", None)
                logger.debug(f"{field} field not found for media instance {self.media_instance_id}.")

    def validate_paths_unused(self):
        """
        This method will verify if the image or file path is unused across all media instances.
        """
        for field in self.NATIVE_DJANGO_FIELD_TYPES:
            used_by_media_instances = Media.objects.filter(**{field: self.media_instance.image})

            if used_by_media_instances.exists():
                used_by_media_instances_ids = used_by_media_instances.values_list('id', flat=True)
                raise ValidationError(f"{field} path is used by media instances: {', '.join(used_by_media_instances_ids)}.")

        logger.debug(f"Media instance {self.media_instance_id} is safe to remove. Unused by other media instances.")

    def validate_media_truly_deleted(self):
        """
        This method will verify if the media instance is truly deleted.
        """
        try:
            Media.objects.get(id=self.media_instance_id)
            raise ValidationError(f"Media instance {self.media_instance_id} is not truly deleted.")
        except Media.DoesNotExist:
            # this is what we want.
            pass

        logger.debug(f"Media instance {self.media_instance_id} is truly deleted.")

    def remove_file_from_storage(self, file_path, field):
        """
        This method will remove the file from the storage.
        """
        # Soft remove from file system. Dont error out if it doesnt exist.
        try:
            os.remove(file_path)
        except FileNotFoundError:
            # File already removed.
            logger.debug(f"{field} for {self.media_instance_id} at {file_path} already removed from storage.")
        except TypeError:
            # Happens when the file path is None
            logger.debug(f"{field} for {self.media_instance_id} is None. Cannot remove.")

        if file_path and os.path.exists(file_path):
            raise FailedToCleanupMediaStorage(f"{field} for {self.media_instance_id} at {file_path} still exists in storage.")
        else:
            logger.debug(f"{field} for {self.media_instance_id} at {file_path} removed from storage.")

    def remove_files_from_storage(self):
        """
        This method will remove the files from the storage.
        """
        for field in self.NATIVE_DJANGO_FIELD_TYPES:
            # Do not change the save value.  False means no db-saves = no signals.
            file_path = getattr(self, f"{field}_path")
            self.remove_file_from_storage(file_path, field)

        for field in self.IMAGEKIT_FIELD_TYPES:
            file_path = getattr(self, f"{field}_path")
            self.remove_file_from_storage(file_path, field)

        logger.debug(f"Files for media instance {self.media_instance_id} removed from storage.")

    def run(self):
        """
        This method will run the flow.
        """
        self.set_paths()
        self.validate_paths_unused()
        self.validate_media_truly_deleted()
        self.remove_files_from_storage()
