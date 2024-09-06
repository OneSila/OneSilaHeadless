from media.models import MediaProductThrough, Media
from sales_channels.factories.mixins import RemoteInstanceCreateFactory, ProductAssignmentMixin, RemoteInstanceUpdateFactory, RemoteInstanceDeleteFactory


class RemoteMediaProductThroughCreateFactory(RemoteInstanceCreateFactory, ProductAssignmentMixin):
    local_model_class = MediaProductThrough
    has_remote_media_instance = False

    def __init__(self, local_instance, sales_channel):
        super().__init__(local_instance, sales_channel)
        self.remote_product = self.get_remote_product(local_instance.product)

    def preflight_check(self):
        """
        Checks for the presence of remote product and assignment to a website.
        """
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
        pass

    def customize_remote_instance_data(self):
        """
        Customizes remote instance data to include remote image if applicable.
        """
        if self.has_remote_media_instance:
            self.remote_instance_data['remote_image'] = self.remote_image
        return self.remote_instance_data

class RemoteMediaProductThroughUpdateFactory(RemoteInstanceUpdateFactory, ProductAssignmentMixin):
    local_model_class = MediaProductThrough

    def __init__(self, local_instance, sales_channel):
        super().__init__(local_instance, sales_channel)
        self.remote_product = self.get_remote_product(local_instance.product)

    def preflight_check(self):
        """
        Checks for the presence of remote product and assignment to a website.
        """
        if not self.remote_product:
            return False

        if not self.assigned_to_website():
            return False

        return True

class RemoteMediaProductThroughDeleteFactory(RemoteInstanceDeleteFactory, ProductAssignmentMixin):
    local_model_class = MediaProductThrough

    def __init__(self, local_instance, sales_channel):
        super().__init__(local_instance, sales_channel)
        self.remote_product = self.get_remote_product(local_instance.product)

    def preflight_check(self):
        """
        Checks for the presence of remote product and assignment to a website.
        """
        if not self.remote_product:
            return False

        if not self.assigned_to_website():
            return False

        return True


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
