from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Model as BaseModel
import os

from .generate_views import generate_view, VIEW_TYPES, \
    generate_views_list, import_app, get_model_app, \
    discover_models


"""
For the app we need to create:
- schema.queries
- schema.mutations
- schema.subscriptions
- notice to add the added query-types to the main schema file

For each model we need to create:
- schema.types.type
- schema.types.input
- schema.types.filters
- schema.types.ordering
- schema.types.type
- schema.queries
- schema.mutations
- schema.subscriptions
"""


def snake_case_to_camel_case(str): return ''.join([i.capitalize() for i in str.split('_')])


def to_snake_case(str):
    res = [str[0].lower()]
    for c in str[1:]:
        if c in ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
            res.append('_')
            res.append(c.lower())
        else:
            res.append(c)

    return ''.join(res)


def get_model_import(app_name, models):
    model_str = ', '.join(models)
    return f"from {app_name}.models import {model_str}"


def make_model_classname(model, name):
    return f"{model}{name}"


def get_type_import(app_name, models):
    types = [make_model_classname(model, 'Type') for model in models]
    return f"from .types.types import {', '.join(types)}"


def get_input_import(app_name, models):
    types = [f"{make_model_classname(model, 'Input')}, {make_model_classname(model, 'PartialInput')}" for model in models]
    return f"from .types.input import {', '.join(types)}"


def generate_type(app_name, models):
    filter_str = ', '.join([f"{m}Filter" for m in models])
    order_str = ', '.join([f"{m}Order" for m in models])
    content = [
        "from core.schema.core.types.types import type, relay, List, Annotated, lazy",
        "from core.schema.core.mixins import GetQuerysetMultiTenantMixin",
        "",
        get_model_import(app_name, models),
        f"from .filters import {filter_str}",
        f"from .ordering import {order_str}",
        "",
        "",
    ]

    for model in models:
        content.extend([
            f"@type({model}, filters={model}Filter, order={model}Order, pagination=True, fields='__all__')",
            f"class {model}Type(relay.Node, GetQuerysetMultiTenantMixin):",
            "    pass",
            "",
            "",
        ])

    return "\n".join(content)


def generate_input(app_name, models):
    model_str = ', '.join(models)
    filter_str = ', '.join([f"{m}Filter" for m in models])
    order_str = ', '.join([f"{m}Order" for m in models])
    content = [
        "from core.schema.core.types.types import auto",
        "from core.schema.core.types.input import NodeInput, input, partial, List",
        "",
        get_model_import(app_name, models),
        "",
        "",
    ]

    for model in models:
        model_input = [
            f'@input({model}, fields="__all__")',
            f"class {model}Input:",
            "    pass",
            "",
            "",
            f'@partial({model}, fields="__all__")',
            f"class {model}PartialInput(NodeInput):",
            "    pass",
            "",
        ]
        content.extend(model_input)

    return "\n".join(content)


def generate_filters(app_name, models):
    content = [
        "from core.schema.core.types.types import auto",
        "from core.schema.core.types.filters import filter, SearchFilterMixin",
        "",
        get_model_import(app_name, models),
        "",
        "",
    ]

    for model in models:
        filter_type = [
            f"@filter({model})",
            f"class {model}Filter(SearchFilterMixin):",
            "",
            "",
        ]
        content.extend(filter_type)

    return "\n".join(content)


def generate_ordering(app_name, models):
    content = [
        "from core.schema.core.types.ordering import order",
        "from core.schema.core.types.types import auto",
        "",
        get_model_import(app_name, models),
        "",
        "",
    ]

    for model in models:
        order_type = [
            f"@order({model})",
            f"class {model}Order:",
            "    id: auto",
            "",
            "",
        ]
        content.extend(order_type)

    return "\n".join(content)


def generate_schema_init(app_name, models):
    content = (
        f"from .queries import {snake_case_to_camel_case(app_name)}Query\n"
        f"from .mutations import {snake_case_to_camel_case(app_name)}Mutation\n"
        f"from .subscriptions import {snake_case_to_camel_case(app_name)}Subscription\n"
    )
    return content


def generate_queries(app_name, models):
    content = [
        "from core.schema.core.queries import node, connection, DjangoListConnection, type, field",
        get_model_import(app_name, models),
        get_type_import(app_name, models),
        "",
        "",
        "@type(name='Query')",
        f"class {snake_case_to_camel_case(app_name)}Query:",
    ]

    for model in models:
        content.extend([
            f"    {to_snake_case(model)}: {model}Type = node()",
            f"    {to_snake_case(model)}s: DjangoListConnection[{model}Type] = connection()",
            "",
        ])
    return '\n'.join(content)


def generate_mutations(app_name, models):
    content = [
        "from core.schema.core.mutations import create, update, delete, type, List, field",
        get_type_import(app_name, models),
        get_input_import(app_name, models),
        "",
        "",
        "@type(name='Mutation')",
        f"class {snake_case_to_camel_case(app_name)}Mutation:",
    ]

    for model in models:
        content.extend([
            f"    create_{to_snake_case(model)}: {model}Type = create({model}Input)",
            f"    create_{to_snake_case(model)}s: List[{model}Type] = create({model}Input)",
            f"    update_{to_snake_case(model)}: {model}Type = update({model}PartialInput)",
            f"    delete_{to_snake_case(model)}: {model}Type = delete()",
            f"    delete_{to_snake_case(model)}s: List[{model}Type] = delete()",
            "",
        ])

    return '\n'.join(content)


def generate_subscriptions(app_name, models):
    content = [
        "from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber",
        get_model_import(app_name, models),
        get_type_import(app_name, models),
        "",
        "",
        "@type(name='Subscription')",
        f"class {snake_case_to_camel_case(app_name)}Subscription:",
    ]

    for model in models:
        content.extend([
            "    @subscription",
            f"    async def {to_snake_case(model)}(self, info: Info, pk: str) -> AsyncGenerator[{model}Type, None]:",
            f"        async for i in model_subscriber(info=info, pk=pk, model={model}):",
            f"            yield i",
            "",
        ])

    return '\n'.join(content)


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
                discovered_models.append(model.__name__)
        except (TypeError, AttributeError):
            pass

    return discovered_models


def to_add_manually(app_name, models):
    app_cap = snake_case_to_camel_case(app_name)
    content = (
        "Do not forget to import the following statement in the main schema file and add the classes to the appropriate places\n"
        f"from {app_name}.schema import {app_cap}Query, {app_cap}Mutation, {app_cap}Subscription"
    )
    return content


class Command(BaseCommand):
    help = (
        "Print or set the schema for a given app based on it's models."
    )

    def add_arguments(self, parser):
        parser.add_argument("app_names",
            nargs="+",
            type=str,
            help="List of the apps you with to generate urls for - or 'all'."
                            )
        parser.add_argument("-d", "--dryrun",
            action="store_true",
            help="Printing instead of writing to file."
                            )

    def save_to_files(self, app_name, path, content):
        path = os.path.join(app_name, 'schema', path)
        with open(path, 'w') as f:
            f.write(content)

    @staticmethod
    def print_content(path, content):
        print(f"# Save to: {path}")
        print(content)

    def handle(self, *args, **options):
        write_output = not options["dryrun"]

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
                models = discover_models(app_name)

                if write_output:
                    self.save_to_files(
                        app_name,
                        'subscriptions.py',
                        generate_subscriptions(app_name, models),
                    )
                    self.save_to_files(
                        app_name,
                        'mutations.py',
                        generate_mutations(app_name, models),
                    )
                    self.save_to_files(
                        app_name,
                        'queries.py',
                        generate_queries(app_name, models),
                    )
                    self.save_to_files(
                        app_name,
                        '__init__.py',
                        generate_schema_init(app_name, models),
                    )
                    self.save_to_files(
                        app_name,
                        'subscriptions.py',
                        generate_subscriptions(app_name, models),
                    )
                    self.save_to_files(
                        app_name,
                        'types/ordering.py',
                        generate_ordering(app_name, models),
                    )

                    self.save_to_files(
                        app_name,
                        'types/filters.py',
                        generate_filters(app_name, models),
                    )

                    self.save_to_files(
                        app_name,
                        'types/input.py',
                        generate_input(app_name, models),
                    )

                    self.save_to_files(
                        app_name,
                        'types/types.py',
                        generate_type(app_name, models),
                    )

                    self.stdout.write(
                        self.style.SUCCESS(f"Wrote {app_name} schema")
                    )
                    self.stdout.write(
                        self.style.SUCCESS(to_add_manually(app_name, models))
                    )

                else:
                    self.print_content(
                        'subscriptions.py',
                        generate_subscriptions(app_name, models),
                    )
                    self.print_content(
                        'mutations.py',
                        generate_mutations(app_name, models),
                    )
                    self.print_content(
                        'queries.py',
                        generate_queries(app_name, models),
                    )
                    self.print_content(
                        '__init__.py',
                        generate_schema_init(app_name, models),
                    )
                    self.print_content(
                        'subscriptions.py',
                        generate_subscriptions(app_name, models),
                    )
                    self.print_content(
                        'types/ordering.py',
                        generate_ordering(app_name, models),
                    )

                    self.print_content(
                        'types/filters.py',
                        generate_filters(app_name, models),
                    )

                    self.print_content(
                        'types/input.py',
                        generate_input(app_name, models),
                    )

                    self.print_content(
                        'types/types.py',
                        generate_type(app_name, models),
                    )
