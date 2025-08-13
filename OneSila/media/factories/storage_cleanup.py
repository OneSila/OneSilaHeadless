from media.models import Media
from core.exceptions import ValidationError
from pathlib import Path
import os
from media.exceptions import FailedToCleanupMediaStorage, NotSafeToRemoveError
from django.conf import settings
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
        This is in theory no possible, but is used as a safety check none the less.
        """
        exists_in_db = False
        for field in self.NATIVE_DJANGO_FIELD_TYPES:
            full_path = getattr(self, f"{field}_path")

            if full_path:
                rel_path = str(Path(full_path).relative_to(settings.MEDIA_ROOT))
                used_by_media_instances = Media.objects.filter(**{f"{field}__endswith": rel_path})

                if used_by_media_instances.exists():
                    exists_in_db = True
                    used_by_media_instances_ids = [str(i) for i in used_by_media_instances.values_list('id', flat=True)]
                    logger.debug(f"{field} {full_path} is used by media instances: {', '.join(used_by_media_instances_ids)}.")
                else:
                    logger.debug(f"{field} {full_path} is not used by any media instances.")
            else:
                logger.debug(f"{field} path is None. Cannot validate. Moving to next field if there is one.")

        if exists_in_db:
            raise NotSafeToRemoveError(f"Media instance {self.media_instance_id} is not safe to remove. It is used by other media instances.")

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
        except Exception as e:
            logger.error(f"Error removing {field} for {self.media_instance_id} at {file_path}: {e}")
            raise FailedToCleanupMediaStorage(f"{field} for {self.media_instance_id} at {file_path} still exists in storage.") from e

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
        self.validate_media_truly_deleted()
        self.validate_paths_unused()
        self.remove_files_from_storage()
