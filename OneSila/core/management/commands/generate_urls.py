from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.models import Model as BaseModel
from .generate_views import generate_view, VIEW_TYPES, \
    generate_views_list, import_app, get_model_app, \
    discover_models
from .generate_views import Command as CustomBaseCommand
import os
import shutil
import importlib


def generate_view_import_statement(models):
    view_names = generate_views_list(models)
    view_str = ', '.join(view_names)
    statement = (
        "from django.urls import path\n"
        f"from .views import {view_str}\n\n"
    )
    return statement


def generate_paths(model):
    name_model = model.__name__
    name_plural = model._meta.verbose_name_plural
    name = model._meta.verbose_name

    url_name = name_plural.replace(' ', '-').lower()
    path_name_plural = name_plural.replace(' ', '_').lower()
    path_name_singular = name.replace(' ', '_').lower()

    return [
        f"    path('{url_name}/', {name_model}ListView.as_view(), name='{path_name_plural}_list'),",
        f"    path('{url_name}/<str:pk>/', {name_model}DetailViev.as_view(), name='{path_name_singular}_detail'),",
        f"    path('{url_name}/<str:pk>/update/', {name_model}UpdateView.as_view(), name='{path_name_singular}_update'),",
        f"    path('{url_name}/<str:pk>/delete/', {name_model}DeleteView.as_view(), name='{path_name_singular}_delete'),",
    ]


def generate_path_statement(models, app_name):
    paths = []

    for model in models:
        paths.extend(generate_paths(model))

    path_str = '\n'.join(paths)

    statement = (
        f"app_name = '{app_name}'\n\n"
        "urlpatterns = [\n"
        f"{path_str}\n"
        "]\n"
    )
    return statement


class Command(CustomBaseCommand):
    help = (
        "Print or set the urls for a given app based on it's models."
    )

    def generate_full_statement(self, app_name):
        models = discover_models(app_name)
        import_statement = generate_view_import_statement(models)
        path_statement = generate_path_statement(models, app_name)

        return import_statement + path_statement

    def generate_path(self, app_name):
        return os.path.join(app_name, 'urls.py')
