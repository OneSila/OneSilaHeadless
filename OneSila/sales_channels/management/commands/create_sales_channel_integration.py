import os
import re
import shutil
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Creates a new sales channel integration with the proper folder structure'

    # Template strings moved to class variables at the bottom
    APPS_PY_TEMPLATE = '''from django.apps import AppConfig


class {class_name}Config(AppConfig):
    name = 'sales_channels.integrations.{integration_name}'
    default_auto_field = 'django.db.models.BigAutoField'
    verbose_name = '{class_name} Integration'
'''

    MODELS_PY_TEMPLATE = '''# Create all of your mirror-models in the model structure.
# Keep it clean, and split out files if you need to.
# This will depend on the structure of the remote locaion.

from django.db import models
from sales_channels.models import SalesChannel, RemoteProduct


class {class_name}SalesChannel(SalesChannel):
    """
    {class_name} sales channel model
    Add {class_name}-specific fields here
    """
    api_url = models.URLField(help_text="{class_name} API URL")
    api_key = models.CharField(max_length=255, help_text="{class_name} API Key")
    api_secret = models.CharField(max_length=255, help_text="{class_name} API Secret")

    class Meta:
        verbose_name = "{class_name} Sales Channel"
        verbose_name_plural = "{class_name} Sales Channels"


class {class_name}Product(RemoteProduct):
    """
    {class_name} product model
    Add {class_name}-specific fields here
    """
    remote_id = models.CharField(max_length=255, help_text="{class_name} product ID")

    class Meta:
        verbose_name = "{class_name} Product"
        verbose_name_plural = "{class_name} Products"
'''

    ADMIN_PY_TEMPLATE = '''from django.contrib import admin
from .models import {class_name}SalesChannel, {class_name}Product


@admin.register({class_name}SalesChannel)
class {class_name}SalesChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_url', 'is_active')
    search_fields = ('name', 'api_url')
    list_filter = ('is_active',)


@admin.register({class_name}Product)
class {class_name}ProductAdmin(admin.ModelAdmin):
    list_display = ('remote_id', 'product', 'sales_channel')
    search_fields = ('remote_id', 'product__name')
    list_filter = ('sales_channel',)
    raw_id_fields = ('product', 'sales_channel')
'''

    MIXINS_TEMPLATE = '''class Get{class_name}APIMixin:
    """
    Mixin to get authenticated {class_name} API client
    """
    def get_api_client(self):
        """
        Returns an authenticated {class_name} API client

        Override this method with actual {class_name} API client implementation
        """
        # Example implementation (replace with actual code):
        # from some_package import {class_name}Client
        # return {class_name}Client(
        #     api_url=self.sales_channel.api_url,
        #     api_key=self.sales_channel.api_key,
        #     api_secret=self.sales_channel.api_secret
        # )
        raise NotImplementedError("Implement with actual {class_name} API client")
'''

    FACTORY_TEMPLATE = '''from sales_channels.factories import RemoteInstanceCreateFactory, RemoteInstanceUpdateFactory
from ..models import {model_name}
from {model_type_lower}s.models import {model_type}
from ..mixins import Get{class_name}APIMixin


class {model_name}CreateFactory(RemoteInstanceCreateFactory, Get{class_name}APIMixin):
    """
    Factory to create {model_type}s in {class_name}
    """
    local_model_class = {model_type}
    remote_model_class = {model_name}
    api_package_name = '{model_type_lower}'
    api_method_name = 'create'

    field_mapping = {{
        # Map local fields to remote fields
        # 'local_field': 'remote_field',
    }}

    default_field_mapping = {{
        # Default values for fields
        # 'remote_field': 'default_value',
    }}

    def customize_payload(self, payload):
        """
        Customize the API payload before sending
        """
        # Add custom logic here
        return payload

    def serialize_response(self, response):
        """
        Process the API response
        """
        # Add custom processing here
        return response


class {model_name}UpdateFactory(RemoteInstanceUpdateFactory, Get{class_name}APIMixin):
    """
    Factory to update {model_type}s in {class_name}
    """
    local_model_class = {model_type}
    remote_model_class = {model_name}
    api_package_name = '{model_type_lower}'
    api_method_name = 'update'

    field_mapping = {{
        # Map local fields to remote fields
        # 'local_field': 'remote_field',
    }}

    def customize_payload(self, payload):
        """
        Customize the API payload before sending
        """
        # Add custom logic here
        return payload

    def serialize_response(self, response):
        """
        Process the API response
        """
        # Add custom processing here
        return response
'''

    CONSTANTS_TEMPLATE = '''# {class_name} integration constants

# API endpoints
API_VERSION = 'v1'

# Status mappings
ORDER_STATUS_MAPPING = {{
    'pending': 'pending',
    'processing': 'processing',
    'completed': 'completed',
    'cancelled': 'cancelled',
}}

# Field mappings
PRODUCT_TYPE_MAPPING = {{
    'simple': 'simple',
    'configurable': 'variable',
}}
'''

    HELPERS_TEMPLATE = '''# Helper functions for {class_name} integration

def format_product_data(product_data):
    """
    Format product data for {class_name} API
    """
    # Add implementation
    return product_data


def format_order_data(order_data):
    """
    Format order data for {class_name} API
    """
    # Add implementation
    return order_data
'''

    RECEIVERS_TEMPLATE = '''# Signal receivers for {class_name} integration
from django.dispatch import receiver
from sales_channels.signals import sales_channel_created, sales_channel_updated
from .models import {class_name}SalesChannel


@receiver(sales_channel_created, sender={class_name}SalesChannel)
def handle_sales_channel_created(sender, instance, **kwargs):
    """
    Handle {class_name} sales channel created
    """
    # Add implementation for when a new {class_name} sales channel is created
    pass


@receiver(sales_channel_updated, sender={class_name}SalesChannel)
def handle_sales_channel_updated(sender, instance, **kwargs):
    """
    Handle {class_name} sales channel updated
    """
    # Add implementation for when a {class_name} sales channel is updated
    pass
'''

    SIGNALS_TEMPLATE = '''# Integration-specific signals can be defined here
from django.dispatch import Signal

# Example signals (uncomment if needed):
# integration_connected = Signal()
# integration_disconnected = Signal()
'''

    TASKS_TEMPLATE = '''# Asynchronous tasks for {class_name} integration
from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task
from .models import {class_name}SalesChannel


@db_task()
def sync_products(sales_channel_id):
    """
    Sync products from {class_name}
    """
    try:
        sales_channel = {class_name}SalesChannel.objects.get(id=sales_channel_id)
        # Add implementation
    except {class_name}SalesChannel.DoesNotExist:
        pass


@db_task()
def sync_orders(sales_channel_id):
    """
    Sync orders from {class_name}
    """
    try:
        sales_channel = {class_name}SalesChannel.objects.get(id=sales_channel_id)
        # Add implementation
    except {class_name}SalesChannel.DoesNotExist:
        pass


@db_periodic_task(crontab(minute='*/30'))
def scheduled_product_sync():
    """
    Scheduled task to sync products every 30 minutes
    """
    for sales_channel in {class_name}SalesChannel.objects.filter(is_active=True):
        sync_products(sales_channel.id)


@db_periodic_task(crontab(minute='*/15'))
def scheduled_order_sync():
    """
    Scheduled task to sync orders every 15 minutes
    """
    for sales_channel in {class_name}SalesChannel.objects.filter(is_active=True):
        sync_orders(sales_channel.id)
'''

    DOCUMENTS_TEMPLATE = '''# Document model definitions for search indexing
# Example:
# from django_elasticsearch_dsl import Document, fields
# from django_elasticsearch_dsl.registries import registry
# from .models import SomeModel
#
# @registry.register_document
# class SomeModelDocument(Document):
#     class Index:
#         name = 'some_models'
#
#     class Django:
#         model = SomeModel
#         fields = ['field1', 'field2']
'''

    URLS_TEMPLATE = '''from django.urls import path
from . import views

app_name = 'integration'

urlpatterns = [
    # Add URLs as needed
    # path('webhook/', views.webhook, name='webhook'),
]
'''

    def add_arguments(self, parser):
        parser.add_argument('integration_name', type=str, help='Name of the integration (e.g. shopify, prestashop)')

    def _get_class_name(self, integration_name):
        """Convert snake_case integration name to PascalCase class name"""
        return ''.join(word.capitalize() for word in integration_name.split('_'))

    def handle(self, *args, **options):
        integration_name = options['integration_name'].lower()

        # Validate integration name
        if not re.match(r'^[a-z0-9_]+$', integration_name):
            raise CommandError('Integration name must contain only lowercase letters, numbers, and underscores')

        # Ensure the sales_channels/integrations directory exists
        integrations_dir = os.path.join(settings.APP_ROOT, 'OneSila', 'sales_channels', 'integrations')
        integration_path = os.path.join(integrations_dir, integration_name)

        # Check if the integration directory already exists
        if os.path.exists(integration_path):
            self.stdout.write(self.style.WARNING(f'Integration directory {integration_path} already exists.'))
        else:
            os.makedirs(integration_path, exist_ok=True)

        self.stdout.write(self.style.SUCCESS(f'Created integration directory {integration_path}'))

        # Use Django's startapp command to create base app structure
        call_command(
            'startapp',
            integration_name,
            os.path.join('sales_channels', 'integrations', integration_name)
        )

        # Create additional directories needed
        dirs_to_create = [
            'factories',
            'models',
            'tests',
            'flows',
            'schema',
        ]

        for directory in dirs_to_create:
            dir_path = os.path.join(integration_path, directory)
            os.makedirs(dir_path, exist_ok=True)
            # Create __init__.py in each directory
            with open(os.path.join(dir_path, '__init__.py'), 'w') as f:
                f.write('')

        # Create additional files with template content
        self._create_file(integration_path, 'constants.py', self._get_constants_template(integration_name))
        self._create_file(integration_path, 'helpers.py', self._get_helpers_template(integration_name))
        self._create_file(integration_path, 'mixins.py', self._get_mixins_template(integration_name))
        self._create_file(integration_path, 'receivers.py', self._get_receivers_template(integration_name))
        self._create_file(integration_path, 'signals.py', self._get_signals_template())
        self._create_file(integration_path, 'tasks.py', self._get_tasks_template(integration_name))
        self._create_file(integration_path, 'defaults.py', '')
        self._create_file(integration_path, 'decorators.py', '')
        self._create_file(integration_path, 'documents.py', self._get_documents_template())
        self._create_file(integration_path, 'exceptions.py', '')
        self._create_file(integration_path, 'urls.py', self._get_urls_template())

        # Update the apps.py file
        self._update_apps_py(integration_path, integration_name)

        # Create a basic models.py file
        self._update_models_py(integration_path, integration_name)

        # Create factory files
        factories_path = os.path.join(integration_path, 'factories')
        self._create_file(factories_path, 'products.py', self._get_factory_template(integration_name, 'Product'))
        self._create_file(factories_path, 'orders.py', self._get_factory_template(integration_name, 'Order'))

        # Update admin.py
        self._update_admin_py(integration_path, integration_name)

        self.stdout.write(self.style.SUCCESS(f'Successfully created {integration_name} integration!'))
        self.stdout.write(f'Remember to add "sales_channels.integrations.{integration_name}" to INSTALLED_APPS in your settings.')

    def _create_file(self, path, filename, content):
        """Helper to create a file with given content"""
        file_path = os.path.join(path, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path

    def _update_apps_py(self, integration_path, integration_name):
        """Update the apps.py file with proper configuration"""
        class_name = self._get_class_name(integration_name)
        content = self.APPS_PY_TEMPLATE.format(
            class_name=class_name,
            integration_name=integration_name
        )
        self._create_file(integration_path, 'apps.py', content)

    def _update_models_py(self, integration_path, integration_name):
        """Update the models.py file with base model structure"""
        class_name = self._get_class_name(integration_name)
        content = self.MODELS_PY_TEMPLATE.format(class_name=class_name)
        self._create_file(integration_path, 'models.py', content)

    def _update_admin_py(self, integration_path, integration_name):
        """Update the admin.py file with model registrations"""
        class_name = self._get_class_name(integration_name)
        content = self.ADMIN_PY_TEMPLATE.format(class_name=class_name)
        self._create_file(integration_path, 'admin.py', content)

    def _get_mixins_template(self, integration_name):
        """Template for mixins.py"""
        class_name = self._get_class_name(integration_name)
        return self.MIXINS_TEMPLATE.format(class_name=class_name)

    def _get_factory_template(self, integration_name, model_type):
        """Template for factory files"""
        class_name = self._get_class_name(integration_name)
        model_name = f"{class_name}{model_type}"
        model_type_lower = model_type.lower()
        return self.FACTORY_TEMPLATE.format(
            class_name=class_name,
            model_name=model_name,
            model_type=model_type,
            model_type_lower=model_type_lower
        )

    def _get_constants_template(self, integration_name):
        """Template for constants.py"""
        class_name = self._get_class_name(integration_name)
        return self.CONSTANTS_TEMPLATE.format(class_name=class_name)

    def _get_helpers_template(self, integration_name):
        """Template for helpers.py"""
        class_name = self._get_class_name(integration_name)
        return self.HELPERS_TEMPLATE.format(class_name=class_name)

    def _get_receivers_template(self, integration_name):
        """Template for receivers.py"""
        class_name = self._get_class_name(integration_name)
        return self.RECEIVERS_TEMPLATE.format(class_name=class_name)

    def _get_signals_template(self):
        """Template for signals.py"""
        return self.SIGNALS_TEMPLATE

    def _get_tasks_template(self, integration_name):
        """Template for tasks.py"""
        class_name = self._get_class_name(integration_name)
        return self.TASKS_TEMPLATE.format(class_name=class_name)

    def _get_documents_template(self):
        """Template for documents.py"""
        return self.DOCUMENTS_TEMPLATE

    def _get_urls_template(self):
        """Template for urls.py"""
        return self.URLS_TEMPLATE
