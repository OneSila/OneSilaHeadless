from media.models import MediaProductThrough, Media
from products.models import Product
from properties.models import ProductProperty
from sales_channels.factories.mixins import IntegrationInstanceOperationMixin, RemoteInstanceDeleteFactory
import logging

from sales_channels.models import RemoteLog, SalesChannel, RemoteImageProductAssociation
from sales_channels.models.products import RemoteProductConfigurator, RemoteProduct
from sales_channels.models.sales_channels import RemoteLanguage, SalesChannelViewAssign

logger = logging.getLogger(__name__)

class RemoteProductSyncFactory(IntegrationInstanceOperationMixin):
    remote_model_class = None  # This should be set in subclasses

    remote_image_assign_create_factory = None
    remote_image_assign_update_factory = None
    remote_image_assign_delete_factory = None

    remote_product_property_class = None
    remote_product_property_create_factory = None
    remote_product_property_update_factory = None
    remote_product_property_delete_factory = None

    sync_product_factory = None
    create_product_factory = None
    delete_product_factory = None
    add_variation_factory = None
    accepted_variation_already_exists_error = None

    field_mapping = {}  # Mapping of local fields to remote fields, should be overridden in subclasses

    api_package_name = 'products'  # The package name (e.g., 'products')
    api_method_name = 'update'  # The method name (e.g., 'update')

    # Remote product types, to be set in specific layer implementations
    REMOTE_TYPE_SIMPLE = None
    REMOTE_TYPE_CONFIGURABLE = None

    def __init__(self, sales_channel: SalesChannel, local_instance: Product,
                 api=None, remote_instance=None, parent_local_instance=None, remote_parent_product=None):
        self.local_instance = local_instance  # Instance of the Product model
        self.sales_channel = sales_channel   # Sales channel associated with the sync
        self.integration = sales_channel # to make it work with other mixins
        self.api = api
        self.parent_local_instance = parent_local_instance  # Optional: parent product instance for variations
        self.remote_parent_product = remote_parent_product  # Optional: If it comes from a  create factory of configurable it will save some queries
        self.remote_instance = remote_instance  # Optional: If it comes from a sync factory of configurable it will save some queries
        self.is_variation = parent_local_instance is not None  # Determine if this is a variation
        self.payload = {}
        self.remote_product_properties = []


    def set_local_assigns(self):
        to_assign = SalesChannelViewAssign.objects.filter(product=self.local_instance, sales_channel=self.sales_channel, remote_product__isnull=True)
        for assign in to_assign:
            assign.remote_product = self.remote_instance
            assign.save()

    def preflight_check(self):
        return True
    
    def should_continue_after_initialize(self):
        """
        Determines whether the process should continue.
        Can be overridden in subclasses to control the flow.
        """
        return True

    def add_field_in_payload(self, field_name, value):
        """
        Sets a value in the payload based on the field mapping.

        :param field_name: The local field name to look up in the field mapping.
        :param value: The value to set in the payload if the field mapping exists.
        """
        remote_key = self.field_mapping.get(field_name, None)
        if remote_key:
            self.payload[remote_key] = value

    def initialize_remote_product(self):
        """
        Attempts to retrieve the remote product instance. If not found, it should
        be created by subclasses implementing the creation logic.
        """
        if self.remote_instance is not None:
            return

        remote_parent_product = None
        if self.is_variation:

            if self.remote_parent_product is not None:
                remote_parent_product = self.remote_parent_product
            else:
                remote_parent_product = self.remote_model_class.objects.get(local_instance=self.parent_local_instance, sales_channel=self.sales_channel)

        self.remote_instance = self.remote_model_class.objects.get(
            local_instance=self.local_instance,
            remote_parent_product=remote_parent_product,
            is_variation=self.is_variation,
            sales_channel=self.sales_channel
        )

    def set_rule(self):
        """
        Sets the product rule for the current local instance.
        If no rule is found, raises a ValueError as the rule is required.
        """
        self.rule = self.local_instance.get_product_rule()

        if not self.rule:
            raise ValueError(f"Product rule is required for {self.local_instance.name}. "
                             f"Please ensure that the product has an associated rule before syncing.")

    def set_product_properties(self):
        """
        Retrieves and sets the required and optional properties for the product.
        Raises an exception if no properties are found, as properties are mandatory for the sync process.
        """
        reule_properties_ids = self.local_instance.get_required_and_optional_properties(product_rule=self.rule).values_list('property_id', flat=True)
        self.product_properties = ProductProperty.objects.filter_multi_tenant(self.sales_channel.multi_tenant_company). \
            filter(product=self.local_instance, property_id__in=reule_properties_ids)

    def process_product_properties(self):
        """
        Processes each property retrieved from the product and performs the necessary actions,
        such as adding to payload, creating or updating remote instances, etc.
        """
        existing_remote_property_ids = []

        for product_property in self.product_properties:
            # Attempt to process the product property
            remote_property_id = self.process_single_property(product_property)
            existing_remote_property_ids.append(remote_property_id)

        # Delete any remote properties that no longer exist locally
        self.delete_non_existing_remote_product_property(existing_remote_property_ids)

    def process_single_property(self, product_property):
        """
        Processes a single product property. Attempts to update if it exists, otherwise creates it.
        Also checks if the property needs to be updated and adds it to remote_product_properties.

        :param product_property: The product property to process.
        :return: The remote product property ID.
        """
        # Try to fetch an existing remote product property
        try:
            remote_property = self.remote_product_property_class.objects.get(
                local_instance=product_property,
                remote_product=self.remote_instance,
                sales_channel=self.sales_channel
            )

            # Run the update factory in get_value_only mode
            update_factory = self.remote_product_property_update_factory(
                local_instance=product_property,
                sales_channel=self.sales_channel,
                remote_product=self.remote_instance,
                remote_instance=remote_property,
                api=self.api,
                get_value_only=True,
                skip_checks=True,
            )
            update_factory.run()

            # If the remote property needs an update, modify the remote instance and its value
            if remote_property.needs_update(update_factory.remote_value):
                remote_property.remote_value = update_factory.remote_value
                remote_property.save()
                self.remote_product_properties.append(remote_property)
                return remote_property.id

        except self.remote_product_property_class.DoesNotExist:
            # If the remote product property does not exist, create it
            create_factory = self.remote_product_property_create_factory(
                local_instance=product_property,
                sales_channel=self.sales_channel,
                remote_product=self.remote_instance,
                api=self.api,
                get_value_only=True,
                skip_checks=True,
            )
            create_factory.run()

            # Add the newly created remote product property to the list
            self.remote_product_properties.append(create_factory.remote_instance)
            return create_factory.remote_instance.id

        # If the remote property does not need updating, return its ID
        return remote_property.id

    def delete_non_existing_remote_product_property(self, existing_remote_property_ids):
        """
        Deletes remote product properties that exist in the remote system but are no longer present locally.

        :param existing_remote_property_ids: The list of existing remote property IDs to keep.
        """
        # Find remote product properties that are not in the list of existing IDs
        remote_properties_to_delete = self.remote_product_property_class.objects.filter(
            remote_product=self.remote_instance,
            sales_channel=self.sales_channel
        ).exclude(id__in=existing_remote_property_ids)

        # Run the delete factory for each property that needs to be removed
        for remote_property in remote_properties_to_delete:
            delete_factory = self.remote_product_property_delete_factory(
                local_instance=remote_property.local_instance,
                sales_channel=self.sales_channel,
                remote_instance=remote_property,
                remote_product=self.remote_instance,
                api=self.api
            )
            delete_factory.run()

    def set_type(self):
        """
        Determines the remote product type based on the local product type
        and sets it in the payload.
        """
        local_type = self.local_instance.type

        if local_type == Product.CONFIGURABLE:
            self.remote_type = self.REMOTE_TYPE_CONFIGURABLE
        else:
            # All other types default to simple
            self.remote_type = self.REMOTE_TYPE_SIMPLE

        self.add_field_in_payload('type', self.remote_type)
        logger.debug(f"Set remote type for {self.local_instance.name}: {self.remote_type}")

    def set_name(self):
        """
        Sets the name for the product or variation in the payload.
        For variations, it delegates to set_variation_name.
        """
        self.name = self.local_instance.name

        if self.is_variation:
            self.set_variation_name()

        self.add_field_in_payload('name', self.name)

    def set_variation_name(self):
        """
        Sets the name for variations by appending parent product name and variation attributes.
        This method can be overridden for custom naming logic for variations.
        """
        if self.is_variation and self.sales_channel.use_configurable_name:
            self.name = self.parent_local_instance.name

    def set_sku(self):
        """Sets the SKU for the product or variation in the payload."""
        self.sku = self.local_instance.sku

        if self.is_variation:
            self.set_variation_sku()

        self.add_field_in_payload('sku', self.sku)

    def set_variation_sku(self):
        """Sets the SKU for variations, defaulting to parent_sku-child_sku."""
        self.sku = f"{self.parent_local_instance.sku}-{self.local_instance.sku}"

    def set_visibility(self):
        """Sets the visibility for the product or variation in the payload."""
        pass # this is needed only for some of the integrations so we don't have a clear way to get it (type dependend)

    def set_variation_visibility(self):
        """Sets the visibility for variations, allowing for overrides."""
        pass

    def set_active(self):
        """Sets the status for the product or variation in the payload."""
        self.active = self.local_instance.active

        if self.is_variation:
            self.set_variation_active()

        self.add_field_in_payload('active', self.active)

    def set_variation_active(self):
        """Sets the status for variations, allowing for overrides."""
        pass

    def set_stock(self):
        """Sets the stock for the product or variation in the payload."""

        return # @TODO: Come back after we decide with inventory
        self.stock = self.local_instance.inventory.salable()

        if self.is_variation:
            self.set_variation_stock()

        self.add_field_in_payload('stock', self.stock)

    def set_variation_stock(self):
        """Sets the stock for variations, allowing for overrides."""
        pass

    def set_content(self):
        """Sets the content fields for the product or variation in the payload."""
        # Set URL key
        self.set_url_key()

        if not self.sales_channel.sync_contents:
            return

        # Set short description
        self.set_short_description()

        # Set full description
        self.set_description()

    def set_short_description(self):
        """Sets the short description for the product or variation in the payload."""
        self.short_description = self.local_instance._get_translated_value(
            field_name='short_description', related_name='translations')

        if self.is_variation:
            self.set_variation_short_description()

        self.add_field_in_payload('short_description', self.short_description)

    def set_variation_short_description(self):
        """Sets the short description for variations, allowing for overrides."""
        pass

    def set_description(self):
        """Sets the description for the product or variation in the payload."""
        self.description = self.local_instance._get_translated_value(
            field_name='description', related_name='translations')

        if self.is_variation:
            self.set_variation_description()

        self.add_field_in_payload('description', self.description)

    def set_variation_description(self):
        """Sets the description for variations, allowing for overrides."""
        pass

    def set_url_key(self):
        """Sets the URL key for the product or variation in the payload."""
        self.url_key = self.local_instance._get_translated_value(field_name='url_key', related_name='translations')

        if self.is_variation:
            self.set_variation_url_key()

        self.add_field_in_payload('url_key', self.url_key)

    def set_variation_url_key(self):
        """Sets the URL key for variations, allowing for overrides."""
        self.url_key = f"{self.url_key}-{self.sku}"

    def set_variation_content(self):
        """Sets the content for variations, allowing for overrides."""
        pass

    def set_ean_code(self):
        """Sets the EAN code for the product or variation in the payload."""
        self.ean_code = self.local_instance.ean_code

        if self.is_variation:
            self.set_variation_ean_code()

        self.add_field_in_payload('ean_code', self.ean_code)

    def set_variation_ean_code(self):
        """Sets the EAN code for variations, allowing for overrides."""
        pass

    def set_categories(self):
        """Sets the categories for the product or variation in the payload."""
        pass # @TODO: Pass for now

    def set_variation_categories(self):
        """Sets the categories for variations, allowing for overrides."""
        pass

    def set_assigns(self):
        """Sets the assigns for the product or variation in the payload."""
        # we will pass this because some integrations will need the product created to set it before. Some others will not so we need to override this
        pass

    def set_variation_assigns(self):
        """Sets the assigns for variations, allowing for overrides."""
        pass

    def set_price(self):
        """Sets the price for the product or variation in the payload."""
        self.price, self.discount = self.local_instance.get_price_for_sales_channel(self.sales_channel)

        # Convert price and discount to float if they are not None
        if self.price is not None:
            self.price = float(self.price)
        if self.discount is not None:
            self.discount = float(self.discount)

        if self.is_variation:
            self.set_variation_price()

        self.add_field_in_payload('price', self.price)
        self.add_field_in_payload('discount', self.discount)

    def set_variation_price(self):
        """Sets the price for variations, allowing for overrides."""
        pass

    def set_allow_backorder(self):
        """
        Sets the allow backorders setting for the product or variation in the payload.
        """
        self.allow_backorder = self.local_instance.allow_backorder

        if self.is_variation:
            self.set_variation_allow_backorder()

        self.add_field_in_payload('allow_backorder', self.allow_backorder)

    def build_payload(self):
        """
        Constructs the payload by calling individual setters for various product attributes.
        """
        for field in self.field_mapping:
            setter_method = getattr(self, f"set_{field}", None)
            if setter_method:
                setter_method()
            else:
                logger.warning(f"Setter method set_{field} not found.")

    def set_variation_allow_backorder(self):
        """
        Sets the allow backorders setting for variations, allowing for overrides.
        """
        pass

    def pre_action_process(self):
        """
        Placeholder for any actions to be performed before the main remote action.
        Override this in subclasses if specific pre-action processing is needed.
        """
        pass

    def perform_remote_action(self):
        """
        Implements the remote update logic using the API client.
        This method updates the actual remote object on the external system.
        """
        # Retrieve the API package (e.g., 'properties')
        api_package = getattr(self.api, self.api_package_name, None)
        if not api_package:
            raise ValueError(f"API package '{self.api_package_name}' not found in the API client.")

        # Retrieve the API method (e.g., 'update')
        api_method = getattr(api_package, self.api_method_name, None)
        if not api_method:
            raise ValueError(f"API method '{self.api_method_name}' not found in the API package '{self.api_package_name}'.")

        # Call the API method with the payload
        return api_method(**self.payload)

    def set_discount(self):
        """
        Sets the discount for the product or variation.
        Override this method if discounts were not included in the payload and needed the product to be created first
        """
        pass

    def post_action_process(self):
        """
        Placeholder for any actions to be performed after the main remote action.
        Override this in subclasses if specific post-action processing is needed.
        """
        pass

    def assign_saleschannels(self):
        """
        Assigns the product to sales channels.
        Override this method if sales channel assignments should be included in the payload for specific integrations.
        """
        pass

    def final_process(self):
        """
        Placeholder for any final steps to complete the sync process.
        Override this in subclasses for specific final processing if needed.
        """
        pass

    def process_content_translation(self, short_description, description, url_key, remote_language):
        """
        Processes a single content translation. This method should be overridden in subclasses
        to define how translations are handled (e.g., adding to the payload, sending to an API).

        :param short_description: Translated short description for the remote language.
        :param description: Translated description for the remote language.
        :param url_key: Translated URL key for the remote language.
        :param remote_language: The RemoteLanguage instance for the current translation.
        """
        raise NotImplementedError("Subclasses must implement process_content_translation.")

    def finalize_content_translations(self):
        """
        Placeholder for any final processing steps needed after handling all content translations.
        Override this in subclasses if specific finalization is required.
        """
        pass

    def set_content_translations(self):
        """
        Sets the content translations for the product or variation in all supported languages.
        """
        if not self.sales_channel.sync_contents:
            return

        remote_languages = RemoteLanguage.objects.filter(sales_channel=self.sales_channel)

        for remote_language in remote_languages:
            # Fetch translations for each content field
            short_description = self.local_instance._get_translated_value(
                field_name='short_description',
                language=remote_language.local_instance,
                related_name='translations'
            )

            description = self.local_instance._get_translated_value(
                field_name='description',
                language=remote_language.local_instance,
                related_name='translations'
            )

            url_key = self.local_instance._get_translated_value(
                field_name='url_key',
                language=remote_language.local_instance,
                related_name='translations'
            )

            self.process_content_translation(
                short_description=short_description,
                description=description,
                url_key=url_key,
                remote_language=remote_language
            )

        # Optional: Additional handling or finalization of content translations
        self.finalize_content_translations()

    def assign_images(self):
        """
        Assigns images to the remote product.
        """
        media_throughs = MediaProductThrough.objects.filter(
            product=self.local_instance,
            media__type=Media.IMAGE
        ).order_by('-is_main_image', 'sort_order')

        # For each MediaProductThrough instance, process the image assignment
        existing_remote_images_ids = []
        for media_through in media_throughs:
            # Check if a RemoteImageProductAssociation exists for this media_through
            try:
                remote_image_assoc = RemoteImageProductAssociation.objects.get(
                    local_instance=media_through,
                    remote_product=self.remote_instance,
                    sales_channel=self.sales_channel
                )
                # If exists, use the update factory
                remote_image = self.update_image_assignment(media_through, remote_image_assoc)
            except RemoteImageProductAssociation.DoesNotExist:
                # If does not exist, use the create factory
                remote_image = self.create_image_assignment(media_through)

            existing_remote_images_ids.append(remote_image.id)

        remote_images_to_delete = RemoteImageProductAssociation.objects.filter(
            remote_product=self.remote_instance,
            sales_channel=self.sales_channel
        ).exclude(id__in=existing_remote_images_ids)

        for remote_image in remote_images_to_delete:
            self.delete_image_assignment(remote_image.local_instance, remote_image)

    def create_image_assignment(self, media_through):
        """
        Creates a remote image assignment for the given media_through instance.
        """
        factory = self.remote_image_assign_create_factory(
            local_instance=media_through,
            sales_channel=self.sales_channel,
            skip_checks=True,
            remote_product=self.remote_instance,
            api=self.api
        )
        factory.run()
        return factory.remote_instance

    def update_image_assignment(self, media_through, remote_image_assoc):
        """
        Updates a remote image assignment for the given media_through instance.
        """
        factory = self.remote_image_assign_update_factory(
            local_instance=media_through,
            sales_channel=self.sales_channel,
            remote_instance=remote_image_assoc,
            skip_checks=True,
            remote_product=self.remote_instance,
            api=self.api
        )
        factory.run()
        return factory.remote_instance

    def delete_image_assignment(self, media_through, remote_image_assoc):
        """
        Updates a remote image assignment for the given media_through instance.
        """
        factory = self.remote_image_assign_delete_factory(
            local_instance=media_through,
            sales_channel=self.sales_channel,
            remote_instance=remote_image_assoc,
            skip_checks=True,
            remote_product=self.remote_instance,
            api=self.api
        )
        factory.run()
        return True

    def get_variations(self):
        """
        Fetches all active variations for the current configurable product.
        """
        # Fetch the variation products in a single query
        self.variations = self.local_instance.get_configurable_variations(active_only=True)

        # Log the number of variations found
        logger.debug(f"Found {self.variations.count()} active variations for product {self.local_instance.name}.")

    def set_remote_configurator(self):
        """
        Sets up or updates the RemoteProductConfigurator for the configurable product.
        """
        if hasattr(self.remote_instance, 'configurator'):
            self.configurator = self.remote_instance.configurator
            self.configurator.update_if_needed(rule=self.rule, variations=self.variations, send_sync_signal=False)
        else:
            self.configurator = RemoteProductConfigurator.objects.create_from_remote_product(
                remote_product=self.remote_instance,
                rule=self.rule,
                variations=self.variations
            )
            logger.debug(f"Created new configurator for {self.local_instance.name}")

    def create_or_update_children(self):
        """
        Synchronizes each variation (child product) associated with the configurable product.
        """
        existing_remote_variation_ids = []

        for variation in self.variations:
            # Try to get the remote variation
            try:
                remote_variation = self.remote_model_class.objects.get(
                    local_instance=variation,
                    sales_channel=self.sales_channel,
                    remote_parent_product=self.remote_instance,
                    is_variation=True
                )
                # Update the existing remote variation
                self.update_child(variation, remote_variation)
            except self.remote_model_class.DoesNotExist:
                # Create a new remote variation
                remote_variation = self.create_child(variation)

            # Keep track of existing remote variation IDs
            existing_remote_variation_ids.append(remote_variation.id)

        # After processing all variations, delete any remote variations not in the local set
        self.delete_removed_variations(existing_remote_variation_ids)

    def update_child(self, variation, remote_variation):
        """
        Updates an existing remote variation (child product).
        """
        factory = self.sync_product_factory(
            sales_channel=self.sales_channel,
            local_instance=variation,
            parent_local_instance=self.local_instance,
            remote_parent_product=self.remote_instance,
            remote_instance=remote_variation,
            api=self.api,
        )
        factory.run()

    def create_child(self, variation):
        """
        Creates a new remote variation (child product).
        """
        factory = self.create_product_factory(
            sales_channel=self.sales_channel,
            local_instance=variation,
            parent_local_instance=self.local_instance,
            remote_parent_product=self.remote_instance,
            api=self.api,
        )
        factory.run()
        remote_variation = factory.remote_instance
        return remote_variation

    def add_variation_to_parent(self):
        """
        Adds the remote variation to the remote parent product.
        """
        try:
            factory = self.add_variation_factory(
                sales_channel=self.sales_channel,
                local_instance=self.local_instance,
                parent_product=self.local_instance,
                remote_instance=self.remote_instance,
                remote_parent_product=self.remote_parent_product,
                skip_checks=True,
                api=self.api
            )
            factory.run()
        except self.accepted_variation_already_exists_error:
            pass

    def delete_child(self, remote_variation):
        """
        Deletes a remote variation (child product) that no longer exists locally.
        """
        factory = self.delete_product_factory(
            sales_channel=self.sales_channel,
            local_instance=remote_variation.local_instance,
            api=self.api,
            remote_instance=remote_variation
        )
        factory.run()

    def delete_removed_variations(self, existing_remote_variation_ids):
        """
        Deletes remote variations that are no longer present in the local variations.
        """
        # Get all remote variations linked to this remote parent product, excluding the existing ones
        remote_variations_to_delete = self.remote_model_class.objects.filter(
            remote_parent_product=self.remote_instance,
            sales_channel=self.sales_channel
        ).exclude(id__in=existing_remote_variation_ids)

        for remote_variation in remote_variations_to_delete:
            self.delete_child(remote_variation)

    def run(self):

        if not self.preflight_check():
            logger.debug(f"Preflight check failed for {self.sales_channel}.")
            return

        self.set_api()
        log_identifier = self.get_identifier()

        self.set_type()
        try:
            self.initialize_remote_product()

            if not self.should_continue_after_initialize():
                logger.debug("Process stopped by should_continue_after_initialize() check.")
                return

            self.set_local_assigns()
            self.set_rule() # we put this here since if is not present we will stop the process
            self.build_payload()
            self.set_product_properties()
            self.process_product_properties()
            self.customize_payload()
            self.pre_action_process()
            self.perform_remote_action()
            self.set_discount()
            self.post_action_process()
            self.set_content_translations()
            self.assign_images()
            self.assign_saleschannels()
            if self.remote_type == self.REMOTE_TYPE_CONFIGURABLE:
                self.get_variations()
                self.set_remote_configurator()
                self.create_or_update_children()

            if self.is_variation:
                self.add_variation_to_parent()

            self.final_process()
        except Exception as e:
            self.log_error(e, RemoteLog.ACTION_CREATE, log_identifier, self.payload)
            raise


class RemoteProductUpdateFactory(RemoteProductSyncFactory):

    # this will be the same with the Sync but the run will be slightly changed to perform only the product related changes
    def run(self):
        if not self.preflight_check():
            logger.debug(f"Preflight check failed for {self.sales_channel}.")
            return

        self.set_api()
        log_identifier = self.get_identifier()

        self.set_type()
        try:
            self.initialize_remote_product()
            self.set_rule()
            self.build_payload()
            self.customize_payload()
            self.pre_action_process()
            self.perform_remote_action()
            self.set_discount()
            self.post_action_process()
            self.assign_saleschannels()
            self.final_process()
        except Exception as e:
            self.log_error(e, RemoteLog.ACTION_CREATE, log_identifier, self.payload)
            raise

class RemoteProductCreateFactory(RemoteProductSyncFactory):
    """
    Factory class responsible for creating remote products and their associated data.
    Subclasses RemoteProductSyncFactory to handle creation-specific logic.
    """

    remote_inventory_class = None
    remote_price_class = None
    remote_product_content_class = None
    remote_id_map = 'id'  # Default remote ID mapping to get the remote id from the response
    sync_product_factory = None

    def initialize_remote_product(self):
        """
        Initializes the RemoteProduct instance.
        Handles three cases:
        1. Brand new product.
        2. Product with failed creation (exists locally but not remotely).
        3. Product already exists remotely but not locally.
        4. Product that existed both locally and remotely,
        """
        remote_parent_product = None
        remote_sku = self.local_instance.sku
        if self.is_variation:
            remote_sku = f"{self.parent_local_instance.sku}-{self.local_instance.sku}"
            if self.remote_parent_product is not None:
                remote_parent_product = self.remote_parent_product
            else:
                remote_parent_product = self.remote_model_class.objects.get(
                    local_instance=self.parent_local_instance,
                    sales_channel=self.sales_channel
                )

        # Attempt to get or create the RemoteProduct instance without filtering on remote_id
        self.remote_instance, created = self.remote_model_class.objects.get_or_create(
            local_instance=self.local_instance,
            remote_parent_product=remote_parent_product,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            sales_channel=self.sales_channel,
            is_variation=self.is_variation,
            remote_sku=remote_sku,
        )

        # If the remote_instance has a remote_id, it means it's already linked to a remote product
        if self.remote_instance.remote_id:
            logger.debug(f"RemoteProduct already exists with remote_id: {self.remote_instance.remote_id}")
            self.switch_to_sync = True
            return

        # Try to fetch the remote product from the remote API
        try:
            response = self.get_saleschannel_remote_object(remote_sku)
            remote_data = self.serialize_response(response)
            if remote_data:
                # Remote product exists but wasn't linked locally
                self.remote_instance.remote_id = self.extract_remote_id(remote_data)
                self.remote_instance.remote_sku = self.extract_remote_sku(remote_data)
                self.remote_instance.save()
                logger.debug(f"Linked existing remote product with remote_id: {self.remote_instance.remote_id}")
                # Set flag to switch to sync
                self.switch_to_sync = True
            else:
                # Remote product doesn't exist; proceed with creation
                logger.debug(f"Proceeding with creation of new remote product for {self.local_instance.name}")
        except Exception as e:
            logger.error(f"Error fetching remote product: {e}")
            # Decide whether to proceed with creation or handle the error differently
            # For now, we'll proceed with creation
            logger.debug(f"Proceeding with creation despite error fetching remote product for {self.local_instance.name}")

    def should_continue(self):
        """
        Determines whether the process should continue.
        If switch_to_sync is True, it will instantiate and run the sync factory,
        then return False to stop the create process.
        """
        if self.switch_to_sync:
            logger.debug("Switching to sync flow.")
            self.run_sync_flow()
            return False
        return True

    def run_sync_flow(self):
        """
        Runs the sync/update flow.
        """
        if self.sync_product_factory is None:
            raise ValueError("sync_product_factory must be specified in the RemoteProductCreateFactory.")

        sync_factory = self.sync_product_factory(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            remote_instance=self.remote_instance,
            parent_local_instance=self.parent_local_instance,
            remote_parent_product=self.remote_parent_product,
            api=self.api,
        )
        sync_factory.run()

    def get_saleschannel_remote_object(self, remote_sku):
        """
        Attempts to fetch the remote product using the remote API.
        Should be overridden in subclasses to provide integration-specific logic.
        Returns the remote product data if found, otherwise None.
        """
        raise NotImplementedError("Subclasses must implement get_saleschannel_remote_object method.")

    # Refactor set_remote_id to use extract_remote_id
    def set_remote_id(self, response_data):
        """
        Sets the remote ID based on the response data using the mapping provided.
        """
        self.remote_instance.remote_id = self.extract_remote_id(response_data)

    def extract_remote_id(self, remote_data):
        """
        Extracts the remote_id from the remote_data using the remote_id_map.
        """
        id_path = self.remote_id_map.split('__')
        remote_id = remote_data

        for path in id_path:
            remote_id = remote_id.get(path)
            if remote_id is None:
                break

        if remote_id is None:
            raise ValueError("Could not extract remote_id from remote_data.")
        return remote_id

    def extract_remote_sku(self, remote_data):
        """
        Extracts the remote_sku from the remote_data.
        Override this method if the remote_sku is stored differently in the remote_data.
        """
        return remote_data.get('sku', self.remote_instance.remote_sku)

    # for the next 3 methods we want to make sure we also create the related mirror models for price, stock, content
    def set_content(self):
        super().set_content()

        if self.remote_product_content_class:
            self.remote_instance.content, _ = self.remote_product_content_class.objects.get_or_create(
                remote_product=self.remote_instance,
                sales_channel=self.sales_channel,
                multi_tenant_company=self.sales_channel.multi_tenant_company
            )
            logger.debug(f"Created RemoteProductContent for {self.remote_instance}")


    def set_stock(self):
        super().set_stock()

        if self.remote_inventory_class:
            self.remote_instance.inventory, _ = self.remote_inventory_class.objects.get_or_create(
                remote_product=self.remote_instance,
                quantity=self.stock,
                sales_channel=self.sales_channel,
                multi_tenant_company=self.sales_channel.multi_tenant_company
            )
            logger.debug(f"Created RemoteInventory for {self.remote_instance}")

    def set_price(self):
        super().set_price()

        if self.remote_price_class:
            self.remote_instance.price, _ = self.remote_price_class.objects.get_or_create(
                remote_product=self.remote_instance,
                price=self.price,
                discount_price=self.discount_price if hasattr(self, 'discount_price') else None,
                sales_channel=self.sales_channel,
                multi_tenant_company=self.sales_channel.multi_tenant_company
            )
            logger.debug(f"Created RemotePrice for {self.remote_instance}")

    def perform_non_subclassed_remote_action(self):
        """
        Implements the remote update logic using the API client.
        This method updates the actual remote object on the external system.
        """
        # Retrieve the API package (e.g., 'properties')
        api_package = getattr(self.api, self.api_package_name, None)
        if not api_package:
            raise ValueError(f"API package '{self.api_package_name}' not found in the API client.")

        # Retrieve the API method (e.g., 'update')
        api_method = getattr(api_package, self.api_method_name, None)
        if not api_method:
            raise ValueError(f"API method '{self.api_method_name}' not found in the API package '{self.api_package_name}'.")

        # Call the API method with the payload
        return api_method(**self.payload)

    def perform_remote_action(self):
        """
        Performs the remote create action and updates the RemoteProduct instance with remote_id and remote_sku.
        """
        try:
            # we do perform_non_subclassed_remote_action and not super().perform_remote_action() because in the integrations we will subclass
            # perform_remote_action and change it. The CreateFactory will always subclass the Sync factory so it will try to do the update before create
            response = self.perform_non_subclassed_remote_action()
            response_data = self.serialize_response(response)

            self.set_remote_id(response_data)
            # Extract remote_id and remote_sku from the response
            self.remote_instance.remote_sku = self.sku

            # Save the RemoteProduct instance with updated remote_id and remote_sku
            self.remote_instance.save()
            logger.debug(f"Updated RemoteProduct with remote_id: {self.remote_instance.remote_id} and remote_sku: {self.remote_instance.remote_sku}")

        except Exception as e:
            logger.error(f"Failed to perform remote action for {self.local_instance.name}: {e}")
            raise


class RemoteProductDeleteFactory(RemoteInstanceDeleteFactory):
    local_model_class = Product
    remote_delete_factory = None

    def preflight_process(self):
        for remote_variation in RemoteProduct.objects.filter(remote_parent_product=self.remote_instance).iterator():
            factory = self.remote_delete_factory(sales_channel=self.sales_channel, remote_instance=remote_variation, api=self.api)
            factory.run()