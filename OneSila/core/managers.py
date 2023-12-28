from django.db.models import QuerySet as DjangoQueryset
from django.db.models import Manager as DjangoManager
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.core.exceptions import FieldDoesNotExist
from django.utils.text import smart_split, unescape_string_literal
from django.contrib.auth.models import BaseUserManager
from django.contrib.admin.utils import lookup_spawns_duplicates as lookup_function

from core.exceptions import SearchFailedError

import operator
from functools import reduce

import logging
logger = logging.getLogger(__name__)


class SearchQuerySetMixin:
    def lookup_needs_distinct(self, queryset, orm_lookups):
        """Return True if an orm_lookup requires calling qs.distinct()."""
        return any(
            lookup_function(queryset.model._meta, search_spec)
            for search_spec in orm_lookups
        )

    def get_search_results(self, search_term, search_fields):
        """
        Return a tuple containing a queryset to implement the search
        and a boolean indicating if the results may contain duplicates.

        This code is borrowed from the django-source where it's present in the
        admin, but not in the querysets which feels like a missed opportunity.
        Currently from version 3.2: https://github.com/django/django/blob/stable/3.2.x/django/contrib/admin/options.py

        There have been some changes as this take the queryset internally, and
        if fed the search_fields instead af grabbing them through the request which has been removed.
        """
        queryset = self

        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            # Use field_name if it includes a lookup.
            opts = self.model._meta
            lookup_fields = field_name.split(LOOKUP_SEP)
            # Go through the fields, following all relations.
            prev_field = None
            for path_part in lookup_fields:
                if path_part == 'pk':
                    path_part = opts.pk.name
                try:
                    field = opts.get_field(path_part)
                except FieldDoesNotExist:
                    # Use valid query lookups.
                    if prev_field and prev_field.get_lookup(path_part):
                        return field_name
                else:
                    prev_field = field
                    if hasattr(field, 'get_path_info'):
                        # Update opts to follow the relation.
                        opts = field.get_path_info()[-1].to_opts
            # Otherwise, use the field with icontains.
            return "%s__icontains" % field_name

        may_have_duplicates = False
        opts = self.model._meta
        if search_fields and search_term:
            orm_lookups = [construct_search(str(search_field))
                           for search_field in search_fields]
            for bit in smart_split(search_term):
                if bit.startswith(('"', "'")) and bit[0] == bit[-1]:
                    bit = unescape_string_literal(bit)
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))
            may_have_duplicates |= any(
                self.lookup_needs_distinct(opts, search_spec)
                for search_spec in orm_lookups
            )
        return queryset, may_have_duplicates

    def search(self, search_term):
        try:
            search_fields = self.model._meta.search_terms
        except AttributeError:
            logger.warning("No `search_terms` declared on the model Meta class")
            search_fields = []

        qs, _ = self.get_search_results(search_term, search_fields)
        return qs


class SearchManagerMixin:
    def get_search_results(self, search_term, search_fields):
        return self.get_queryset().get_search_results(search_term, search_fields)

    def search(self, search_term):
        return self.get_queryset().search(search_term)


class MultiTenantUserLoginTokenQuerySet(DjangoQueryset):
    def get_by_token(self, token):
        try:
            instance = self.get(token=token)
        except self.model.DoesNotExist:
            raise ValidationError('Unknown token')

        if not instance.is_valid:
            raise ValidationError('Token is no longer valid')

        return instance


class MultiTenantUserLoginTokenManager(DjangoManager):
    def get_queryset(self):
        return MultiTenantUserLoginTokenQuerySet(self.model, using=self._db)

    def get_by_token(self, token):
        return self.get_queryset().get_by_token(token)


class MultiTenantQuerySet(SearchQuerySetMixin, DjangoQueryset):
    def filter(self, *, multi_tenant_company, **kwargs):
        return super().filter(multi_tenant_company=multi_tenant_company, **kwargs)


class MultiTenantManager(SearchManagerMixin, DjangoManager):
    def get_queryset(self):
        return MultiTenantQuerySet(self.model, using=self._db)

    def create(self, *, multi_tenant_company, **kwargs):
        return super().create(multi_tenant_company=multi_tenant_company, **kwargs)

    def get_or_create(self, *, multi_tenant_company, **kwargs):
        return super().get_or_create(multi_tenant_company=multi_tenant_company, **kwargs)


class MultiTenantUserManager(BaseUserManager):
    """
    A custom user manager to deal with emails as unique identifiers for auth
    instead of usernames. The default that's used is "UserManager"
    """

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class MultiTenantCompanyCreateMixin:
    def create(self, *args, **kwargs):
        multi_tenant_company = kwargs.get('multi_tenant_company')

        if not multi_tenant_company:
            raise IntegrityError("You cannot create without setting a multi_tenant_company value.")

        return super().create(*args, **kwargs)


class QuerySet(SearchQuerySetMixin, DjangoQueryset):
    pass


class Manager(SearchManagerMixin, DjangoManager):
    def get_queryset(self):
        return QuerySet(self.model, using=self._db)


class QuerySetProxyModelMixin:
    """
    Should you wish ot use this mixin for proxy-classes, dont forget to set
    - proxy_filter_field on the model
    """

    def filter(self, *args, **kwargs):
        kwargs.update(self.model.proxy_filter_fields)
        return super().filter(*args, **kwargs)

    def create(self, **kwargs):
        kwargs.update(self.model.proxy_filter_fields)
        return super().create(**kwargs)

    def all(self):
        return self.filter()
