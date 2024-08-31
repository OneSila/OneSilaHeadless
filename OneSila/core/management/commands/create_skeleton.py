from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import shutil


SKELETON_STRUCTURE = [
    'helpers.py',
    'defaults.py',
    'decorators.py',
    'demo_data.py',
    'exceptions.py',
    'tasks.py',
    'flows',
    'flows/__init__.py',
    'factories',
    'factories/__init__.py',
    'signals.py',
    'receivers.py',
    'schema',
    'schema/__init__.py',
    'schema/queries.py',
    'schema/mutations.py',
    'schema/subscriptions.py',
    'schema/types',
    'schema/types/input.py',
    'schema/types/filters.py',
    'schema/types/types.py',
    'schema/types/ordering.py',
    'schema/types/__init__.py',
    'tests',
    'tests/helpers.py',
    'tests/__init__.py',
    'tests/tests_schemas/',
    'tests/tests_schemas/__init__.py',
    'tests/tests_schemas/tests_queries.py',
    'tests/tests_schemas/tests_mutations.py',
    'tests/tests_schemas/tests_subscriptions.py',
    'tests/tests_factories/',
    'tests/tests_factories/__init__.py',
    'tests/tests_flows/',
    'tests/tests_flows/__init__.py',
    'tests/tests_tasks.py',
    'tests/tests_models.py',
    'urls.py',
]


SKELETON_STRUCTURE_DELETE = [
    'tests.py',
]


RECEIVERS_CODE = """
    def ready(self):
        from . import receivers
"""

DEMO_DATA_CODE = """
from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator

registry = DemoDataLibrary()

# # Demo-data generators can be used as method, like the public and private examples below.
# @registry.register_private_app
# def populate_private_some_data(multi_tenant_company):
#     demo_data = {
#         'first_name': faker.first_name()
#         'field_other': (function, {"kwarg": 393}),
#         'field_value': 12121,
#     }
#     baker.make("MyModel", **demo_data)
#
# # A demo-data generator for a public app could look like:
# @registry.register_public_app
# def populate_some_public_data():
#     demo_data = {
#         'first_name': faker.first_name()
#     }
#     baker.make("MyModel", **demo_data)

# # They can also be classes, subclassed from PrivateDataGenerator or PublicDataGenerator
# @registry.register_private_app
# class AppModelPrivateGenerator(PrivateDataGenerator):
#     model = PrivateModel
#     count = 10
#     field_mapper = {
#         'first_name': fake.fist_name,
#         'last_name': fake.last_name,
#    }
#
# @registry.register_public_app
# class AppModelPublicGenerator(PublicDataGenerator):
#     model = PublicModel
#     count = 10
#     field_mapper = {
#         'unit': some_data_generating_method,
#    }
"""


def get_app_path(app_name):
    pwd = os.getcwd()
    app_path = os.path.join(pwd, app_name)
    return app_path


def create_structure(app_name):
    app_path = get_app_path(app_name)

    for bone in SKELETON_STRUCTURE:
        path = os.path.join(app_path, bone)
        is_file = bone[-3:-2] == '.'

        if is_file:
            os.system(f'touch {path}')
        else:
            try:
                os.mkdir(path)
            except FileExistsError:
                pass

    return True


def delete_structure(app_name):
    app_path = get_app_path(app_name)

    for bone in SKELETON_STRUCTURE_DELETE:
        path = os.path.join(app_path, bone)
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass

    return True


def set_code(app_name, filename, string_to_set):
    """
    To ensure signals are correctly interpreted
    in the receivers.py file, we must add a
    snippet to the apps.py file.
    """
    pwd = os.getcwd()
    path = os.path.join(pwd, app_name, filename)

    with open(path, 'r') as f:
        file_contents = f.read()

    if not string_to_set in file_contents:
        with open(path, 'a') as f:
            f.write(string_to_set.strip())

    return True


def set_receiver_code(app_name):
    set_code(app_name, 'apps.py', RECEIVERS_CODE)


def set_demo_data_code(app_name):
    set_code(app_name, 'demo_data.py', DEMO_DATA_CODE)


class Command(BaseCommand):
    help = ("Create the skeleton files and folder structure for a given app_name in the current path. ex: schema, flows,..  \n"
        "Use 'all' to create in every local app")

    def add_arguments(self, parser):
        parser.add_argument("app_names", nargs="+", type=str)

    def handle(self, *args, **options):
        if 'all' in options["app_names"]:
            apps = settings.INSTALLED_LOCAL_APPS
        else:
            apps = options["app_names"]

        for app_name in apps:
            if not os.path.exists(app_name):
                self.stdout.write(
                    self.style.ERROR(f"No such app: {app_name}")
                )
            else:
                create_structure(app_name)
                delete_structure(app_name)
                set_receiver_code(app_name)
                set_demo_data_code(app_name)

                self.stdout.write(
                    self.style.SUCCESS('Created skeleton file and folder structure for "%s"' % app_name)
                )
