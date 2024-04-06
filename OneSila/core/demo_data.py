import importlib

from django.core.exceptions import ValidationError
from django.conf import settings
from model_bakery import baker
from faker import Faker

faker = Faker()


class DemoDataMixin:
    @staticmethod
    def method_name(method):
        return method.__name__

    def register_private_app(self, method):
        method_name = self.method_name(method)

        if self.registry_private_apps.get(method_name):
            raise ValidationError(f"Method {method} is already present in the private app registry. You should pick a unique name.")

        self.registry_private_apps[method_name] = method

    def register_pubic_app(self, method):
        method_name = self.method_name(method)

        if self.registry_public_apps.get(method_name):
            raise ValidationError(f"Method {method} is already present in the public app registry. You should pick a unique name.")

        self.registry_public_apps[method_name] = method

    def load_apps(self):
        # To get the apps to register their demo-data, all we need to do is load the file.
        # upon loading, it will register and add all to the registry.
        for app in settings.INSTALLED_APPS:
            try:
                importlib.import_module(f"{app}.demo_data")
            except ModuleNotFoundError:
                # This approach will try to load demo-data from every app, but
                # this will not always be present - especially on external packages.
                pass

    def populate_db(self, *, multi_tenant_user):
        for method in self.registry_public_apps.values():
            method(multi_tenant_user)

        for method in self.registry_private_apps.values():
            method(multi_tenant_user)

    def run(self, *, multi_tenant_user):
        self.load_apps()
        self.populate_db(multi_tenant_user=multi_tenant_user)


class DemoDataLibrary(DemoDataMixin):
    registry_private_apps = {}
    registry_public_apps = {}
