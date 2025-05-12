from media.models import MediaProductThrough, Media
from sales_channels.factories.mixins import RemoteInstanceCreateFactory, ProductAssignmentMixin, RemoteInstanceUpdateFactory, RemoteInstanceDeleteFactory


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


class RemoteMediaProductThroughCreateFactory(ProductAssignmentMixin, RemoteInstanceCreateFactory):
    local_model_class = MediaProductThrough
    has_remote_media_instance = False

    def __init__(self, sales_channel, local_instance, remote_product, api=None, skip_checks=False):
        super().__init__(sales_channel, local_instance, api=api)
        self.remote_product = remote_product or self.get_remote_product(local_instance.product)

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


class RemoteMediaProductThroughUpdateFactory(ProductAssignmentMixin, RemoteInstanceUpdateFactory):
    local_model_class = MediaProductThrough

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


class RemoteMediaProductThroughDeleteFactory(ProductAssignmentMixin, RemoteInstanceDeleteFactory):
    local_model_class = MediaProductThrough

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
