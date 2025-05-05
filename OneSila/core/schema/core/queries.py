import strawberry_django
from strawberry.relay import from_base64
from strawberry_django.fields.field import StrawberryDjangoField, filter_with_perms, optimizer
from strawberry_django.relay import DjangoListConnection
from strawberry.types import Info
from strawberry import type, field
from typing import Any, List
from .extensions import default_extensions
from .mixins import GetMultiTenantCompanyMixin


class CoreNode(GetMultiTenantCompanyMixin, StrawberryDjangoField):
    """
    Because we override filter methods to ensure that one can only fetch with the
    appropriate multi_tenant_company, we must override this query methods as well.
    """

    def get_queryset_hook(self, info, **kwargs):
        def qs_hook(qs):
            qs = self.get_queryset(qs, info, **kwargs)
            return qs.last()
        return qs_hook

    def get_queryset(self, queryset, info, **kwargs):
        multi_tenant_company = self.get_multi_tenant_company(info, fail_silently=False)
        globalid = kwargs.get('pk')
        _, pk = from_base64(globalid)

        queryset.filter(multi_tenant_company=multi_tenant_company, pk=pk)

        ext = optimizer.optimizer.get()
        if ext is not None:
            queryset = ext.optimize(queryset, info=info)

        return queryset


def anonymous_field(*args, **kwargs):
    return strawberry_django.field(*args, **kwargs)


def field(*args, **kwargs):
    extensions = default_extensions
    return strawberry_django.field(*args, **kwargs, extensions=extensions)


def node(*args, **kwargs):
    extensions = default_extensions
    # return CoreNode(*args, extensions=extensions, **kwargs)
    return strawberry_django.node(*args, extensions=extensions, **kwargs)


def connection(*args, **kwargs):
    extensions = default_extensions
    return strawberry_django.connection(*args, **kwargs, extensions=extensions)
