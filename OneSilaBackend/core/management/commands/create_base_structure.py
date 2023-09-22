from django.core.management.base import BaseCommand, CommandError
import os
import shutil

BASE_STRUCTURE = [
    'helpers.py',
    'defaults.py',
    'decorators.py',
    'exceptions.py',
    'tasks.py',
    'flows',
    'flows/__init__.py',
    'flows/flows.py',
    'factories',
    'factories/__init__.py',
    'factories/factories.py',
    'signals.py',
    'receivers.py',
    'schema',
    'schema/__init__.py',
    'schema/queries.py',
    'schema/mutations.py',
    'schema/types',
    'schema/types/input.py',
    'schema/types/filters.py',
    'schema/types/types.py',
    'schema/types/ordering.py',
    'schema/types/__init__.py',
]

RECEIVERS_CODE = """
    def ready(self):
        from . import receivers
"""


def create_structure(app_name):
    pwd = os.getcwd()
    app_path = os.path.join(pwd, app_name)

    for base in BASE_STRUCTURE:
        path = os.path.join(app_path, base)
        is_file = base[-3:-2] == '.'

        if is_file:
            os.system(f'touch {path}')
        else:
            try:
                os.mkdir(path)
            except FileExistsError:
                pass

    return True


def set_receiver_code(app_name):
    pwd = os.getcwd()
    path = os.path.join(pwd, app_name, 'apps.py')

    with open(path, 'r') as f:
        file_contents = f.read()

    if not RECEIVERS_CODE in file_contents:
        with open(path, 'a') as f:
            f.write(RECEIVERS_CODE)


class Command(BaseCommand):
    help = "Create the base file and folder structure for a given app_name in the current path. ex: schema, flows,.."

    def add_arguments(self, parser):
        parser.add_argument("app_names", nargs="+", type=str)

    def handle(self, *args, **options):
        for app_name in options["app_names"]:
            create_structure(app_name)
            set_receiver_code(app_name)

            self.stdout.write(
                self.style.SUCCESS('Created base file and folder structure for "%s"' % app_name)
            )
