from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.core.exceptions import FieldDoesNotExist
from django.utils.text import smart_split, unescape_string_literal
from django.contrib.admin.utils import lookup_spawns_duplicates

from core.exceptions import SearchFailedError

import operator
from functools import reduce

import logging
logger = logging.getLogger(__name__)


class SearchQuerySetMixin:
    def lookup_needs_distinct(self, queryset, orm_lookups):
        """Return True if an orm_lookup requires calling qs.distinct()."""
        return any(
            lookup_spawns_duplicates(queryset.model._meta, search_spec)
            for search_spec in orm_lookups
        )

    def get_search_results(self, *, search_term, search_fields, multi_tenant_company=None):
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
        if search_term:
            search_term = search_term[:100]

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

        filter_kwargs = {}
        if multi_tenant_company:
            filter_kwargs['multi_tenant_company'] = multi_tenant_company

        if search_fields and search_term:
            orm_lookups = [construct_search(str(search_field)) for search_field in search_fields]

            for bit in smart_split(search_term):
                if bit.startswith(('"', "'")) and bit[0] == bit[-1]:
                    bit = unescape_string_literal(bit)
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]

                queryset = queryset.filter(reduce(operator.or_, or_queries), **filter_kwargs)

            may_have_duplicates |= any(
                self.lookup_needs_distinct(opts, search_spec)
                for search_spec in orm_lookups
            )
        return queryset, may_have_duplicates

    def search(self, search_term, multi_tenant_company=None):
        if search_term:
            search_term = search_term[:100]
        try:
            search_fields = self.model._meta.search_terms
        except AttributeError:
            logger.warning("No `search_terms` declared on the model Meta class")
            search_fields = []

        qs, _ = self.get_search_results(
            search_term=search_term,
            search_fields=search_fields,
            multi_tenant_company=multi_tenant_company)

        return qs.distinct()


class SearchManagerMixin:
    def get_search_results(self, *, search_term, search_fields, multi_tenant_company=None):
        return self.get_queryset().get_search_results(
            search_term=search_term,
            search_fields=search_fields,
            multi_tenant_company=multi_tenant_company
        )

    def search(self, search_term, multi_tenant_company=None):
        return self.get_queryset().search(search_term=search_term, multi_tenant_company=multi_tenant_company)
