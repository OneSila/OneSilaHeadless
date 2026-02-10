from media.models import MediaProductThrough, Media
from sales_channels.factories.mixins import RemoteInstanceCreateFactory, ProductAssignmentMixin, RemoteInstanceUpdateFactory, RemoteInstanceDeleteFactory, RemoteProductSyncRequestMixin
from sales_channels.models import SyncRequest
from integrations.signals import remote_instance_post_create


import logging
logger = logging.getLogger(__name__)


class RemoteMediaCreateFactory(RemoteInstanceCreateFactory):
    local_model_class = Media


class RemoteMediaUpdateFactory(RemoteInstanceUpdateFactory):
    local_model_class = Media


class RemoteImageDeleteFactory(RemoteInstanceDeleteFactory):
    local_model_class = Media
    has_remote_media_instance = False
    delete_media_assign_factory = None

    def run(self):
        """
        Custom run method for handling deletions with or without a remote media instance.
        """
        if self.has_remote_media_instance:
            # Normal delete operation
            super().run()
        else:
            # Custom behavior for deleting all associated media assignments
            media_product_throughs = MediaProductThrough.objects.filter(media=self.local_instance)
            for media_product_through in media_product_throughs:
                delete_factory = self.delete_media_assign_factory(media_product_through, self.sales_channel)
                delete_factory.run()


class RemoteMediaProductThroughCreateFactory(RemoteProductSyncRequestMixin, ProductAssignmentMixin, RemoteInstanceCreateFactory):
    local_model_class = MediaProductThrough
    has_remote_media_instance = False
    sync_request_type = SyncRequest.TYPE_IMAGES
    sync_request_task_kwargs_key = "local_instance_id"

    def __init__(self, sales_channel, local_instance, remote_product, api=None, skip_checks=False):
        super().__init__(sales_channel, local_instance, api=api)
        self.remote_product = remote_product or self.get_remote_product(local_instance.product)

        if skip_checks and self.remote_product is None:
            raise ValueError("Factory has skip checks enabled without providing the remote product.")

        self.skip_checks = skip_checks
        self._existing_remote_assignment = None
        self._current_remote_assignment = None

        remote_model_class = getattr(self, 'remote_model_class', None)

        if remote_model_class and self.remote_product and self.local_instance:
            self._current_remote_assignment = remote_model_class.objects.filter(
                local_instance=self.local_instance,
                sales_channel=self.sales_channel,
                remote_product=self.remote_product,
            ).first()

            if not self._current_remote_assignment and self.local_instance.sales_channel_id:
                self._existing_remote_assignment = self._get_existing_default_remote_assignment()

    def preflight_check(self):
        """
        Checks for the presence of remote product and assignment to a website.
        """
        if self.skip_checks:
            logger.warning("Skipping preflight check for RemoteMediaProductThroughCreateFactory")
            return True

        if not self.remote_product:
            logger.warning("Remote product is not found for RemoteMediaProductThroughCreateFactory")
            return False

        if not self.assigned_to_website():
            logger.warning("Product is not assigned to a website for RemoteMediaProductThroughCreateFactory")
            return False

        return True

    def preflight_process(self):
        """
        Optional process to create remote image instance if applicable.
        """
        if self.has_remote_media_instance:
            self.create_remote_image()

    def create_remote_image(self):
        """
        Placeholder method to create remote image, should be overridden in the third layer.
        """
        raise NotImplementedError("This method should be overridden in the third layer.")

    def customize_remote_instance_data(self):
        """
        Customizes remote instance data to include remote image if applicable.
        """
        if self.has_remote_media_instance:
            self.remote_instance_data['remote_image'] = self.remote_image

        return self.remote_instance_data

    def _get_existing_default_remote_assignment(self):
        default_assignment = MediaProductThrough.objects.filter(
            product=self.local_instance.product,
            media=self.local_instance.media,
            sales_channel__isnull=True,
        ).first()

        if not default_assignment:
            return None

        remote_model_class = getattr(self, 'remote_model_class', None)

        if remote_model_class is None:
            return None

        return remote_model_class.objects.filter(
            local_instance=default_assignment,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        ).select_related('remote_image').first()

    def _reuse_existing_remote_assignment(self):
        if not self._existing_remote_assignment:
            return

        existing_remote_assignment = self._existing_remote_assignment

        if hasattr(existing_remote_assignment, 'remote_image'):
            self.remote_image = existing_remote_assignment.remote_image

        self.build_remote_instance_data()
        self.customize_remote_instance_data()
        self.initialize_remote_instance()

        update_fields = set(self.remote_instance_data.keys())

        for attr in ('remote_id', 'remote_image', 'successfully_created', 'outdated', 'outdated_since'):
            if hasattr(existing_remote_assignment, attr):
                setattr(self.remote_instance, attr, getattr(existing_remote_assignment, attr))
                update_fields.add(attr)

        self.remote_instance.save(update_fields=list(update_fields))

        remote_instance_post_create.send(sender=self.remote_instance.__class__, instance=self.remote_instance)

    def run(self):
        if self._current_remote_assignment:
            if not self.preflight_check():
                return

            self.remote_instance = self._current_remote_assignment
            return

        if self._existing_remote_assignment:
            if not self.preflight_check():
                return

            self._reuse_existing_remote_assignment()
            return

        super().run()


class RemoteMediaProductThroughUpdateFactory(RemoteProductSyncRequestMixin, ProductAssignmentMixin, RemoteInstanceUpdateFactory):
    local_model_class = MediaProductThrough
    sync_request_type = SyncRequest.TYPE_IMAGES
    sync_request_task_kwargs_key = "local_instance_id"

    def __init__(self, sales_channel, local_instance, remote_product, api=None, skip_checks=False, remote_instance=None):
        super().__init__(sales_channel, local_instance, api=api, remote_instance=remote_instance, remote_product=remote_product)

        if skip_checks and self.remote_product is None:
            raise ValueError("Factory has skip checks enabled without providing the remote product.")

        self.skip_checks = skip_checks

    def preflight_check(self):
        """
        Checks for the presence of remote product and assignment to a website.
        """
        if self.skip_checks:
            return True

        if not self.remote_product:
            return False

        if not self.assigned_to_website():
            return False

        return True


class RemoteMediaProductThroughDeleteFactory(RemoteProductSyncRequestMixin, ProductAssignmentMixin, RemoteInstanceDeleteFactory):
    local_model_class = MediaProductThrough
    sync_request_type = SyncRequest.TYPE_IMAGES
    sync_request_task_kwargs_key = "local_instance_id"

    def __init__(self, sales_channel, remote_product, local_instance=None, api=None, skip_checks=False, remote_instance=None):
        super().__init__(sales_channel, local_instance, api=api, remote_instance=remote_instance, remote_product=remote_product)

        if skip_checks and self.remote_product is None:
            raise ValueError("Factory has skip checks enabled without providing the remote product.")

        self.skip_checks = skip_checks

    def preflight_check(self):
        """
        Checks for the presence of remote product and assignment to a website.
        """
        if not self.remote_product:
            return False

        if not self.assigned_to_website():
            return False

        return True
