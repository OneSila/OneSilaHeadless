from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.models import Model as BaseModel
import os
import shutil
import importlib

VIEW_TYPES = ['ListView', 'DetailViev', 'UpdateView', 'DeleteView']


def generate_view(view):
    view = (
        f"class {view}(EmptyTemplateView):\n"
        "    pass\n"

    )
    return view


def generate_model_import_statement(models):
    model_names = [m.__name__ for m in models]
    model_str = ', '.join(model_names)
    statement = (
        "from core.views import EmptyTemplateView\n"
        f"from .models import {model_str}\n\n"
    )
    return statement


def generate_views_list(models):
    return [f"{model.__name__}{view_type}" for model in models for view_type in VIEW_TYPES]


def generate_views_statement(models):
    views = [generate_view(view) for view in generate_views_list(models)]
    return '\n\n'.join(views)


def import_app(app_name):
    return importlib.import_module(app_name)


def get_model_app(model):
    return model.__module__.split('.')[0]


def discover_models(app_name):
    """
    Discover the models in the app, but only from the app.
    So no imported modules.
    """
    app = import_app(app_name)
    app_models = getattr(app, 'models')
    model_names = sorted(dir(app_models))

    discovered_models = []

    for model_name in model_names:
        try:
            model = getattr(app_models, model_name)
            model_app = get_model_app(model)
            if issubclass(model, BaseModel) and model_app == app_name:
                discovered_models.append(model)
        except (TypeError, AttributeError):
            pass

    return discovered_models


class Command(BaseCommand):
    help = (
        "Print or set the views for a given app based on it's models."
    )

    def add_arguments(self, parser):
        parser.add_argument("app_names",
            nargs="+",
            type=str,
            help="List of the apps you with to generate urls for - or 'all'."
                            )
        parser.add_argument("-w", "--write",
            action="store_true",
            help="Write to file instead of printing."
                            )

    def generate_full_statement(self, app_name):
        models = discover_models(app_name)
        import_statement = generate_model_import_statement(models)
        view_statement = generate_views_statement(models)

        return import_statement + view_statement

    def generate_path(self, app_name):
        return os.path.join(app_name, 'views.py')

    def handle(self, *args, **options):
        write_output = options["write"]

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
                statement = self.generate_full_statement(app_name)
                path = self.generate_path(app_name)

                if write_output:
                    with open(path, 'w') as f:
                        f.write(statement)

                    self.stdout.write(
                        self.style.SUCCESS(f"Generated statements added to {path}")
                    )

                else:
                    self.stdout.write(
                        self.style.SUCCESS(statement)
                    )
