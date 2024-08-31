from core.schema.core.mutations import default_extensions, UpdateMutation
from strawberry_django.resolvers import django_resolver
from core.schema.core.mutations import type
from django.db import transaction
from core.schema.core.mutations import Info, Any, models
from products_inspector.models import Inspector
from products_inspector.schema.types.input import InspectorPartialInput
from products_inspector.schema.types.types import InspectorType
from core.schema.core.mixins import GetCurrentUserMixin

def refresh_inepsctor():
    extensions = default_extensions
    return RefreshInspectorMutation(InspectorPartialInput, extensions=extensions)

class RefreshInspectorMutation(UpdateMutation, GetCurrentUserMixin):
    def update(self, info: Info, instance: Inspector, data: dict[str, Any]):
        instance.inspect_product()
        instance.refresh_from_db()
        return instance

@type(name="Mutation")
class InspectorMutation:
    refresh_inepsctor: InspectorType = refresh_inepsctor()
