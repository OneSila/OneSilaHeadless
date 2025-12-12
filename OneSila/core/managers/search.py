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
    def _build_orm_lookups(self, *, search_fields, is_literal):
        def construct_search(field_name):
            if is_literal:
                return "%s__iexact" % field_name

            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]

            opts = self.model._meta
            lookup_fields = field_name.split(LOOKUP_SEP)
            prev_field = None
            for path_part in lookup_fields:
                if path_part == 'pk':
                    path_part = opts.pk.name
                try:
                    field = opts.get_field(path_part)
                except FieldDoesNotExist:
                    if prev_field and prev_field.get_lookup(path_part):
                        return field_name
                else:
                    prev_field = field
                    if hasattr(field, 'get_path_info'):
                        opts = field.get_path_info()[-1].to_opts
            return "%s__icontains" % field_name

        return [construct_search(str(search_field)) for search_field in search_fields]

    def lookup_needs_distinct(self, queryset, orm_lookups):
        """Return True if an orm_lookup requires calling qs.distinct()."""
        return any(
            lookup_spawns_duplicates(queryset.model._meta, search_spec)
            for search_spec in orm_lookups
        )

    def get_search_results(self, *, search_term, search_fields, multi_tenant_company=None):

        queryset = self
        if search_term:
            search_term = search_term[:100]

        filter_kwargs = {}
        if multi_tenant_company:
            filter_kwargs['multi_tenant_company'] = multi_tenant_company

        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)

        if not (search_term and search_fields):
            return queryset, False

        is_literal = False
        if search_term.startswith('"') and search_term.endswith('"') and len(search_term) > 1:
            is_literal = True

        orm_lookups = self._build_orm_lookups(search_fields=search_fields, is_literal=is_literal)
        may_have_duplicates = self.lookup_needs_distinct(self, orm_lookups)

        base_manager = self.model._default_manager.using(queryset.db)

        for bit in smart_split(search_term):
            if bit.startswith(('"', "'")) and bit[0] == bit[-1]:
                bit = unescape_string_literal(bit)

            exists_clauses = []
            for orm_lookup in orm_lookups:
                try:
                    subquery = base_manager.filter(pk=models.OuterRef('pk'), **filter_kwargs, **{orm_lookup: bit}).only('pk')
                except Exception as exc:  # pragma: no cover - consistent error handling
                    raise SearchFailedError(str(exc))

                exists_clauses.append(models.Exists(subquery))

            if not exists_clauses:
                continue

            queryset = queryset.filter(reduce(operator.or_, exists_clauses))

        return queryset, may_have_duplicates

    def get_search_results_old(self, *, search_term, search_fields, multi_tenant_company=None):
        """
        Legacy implementation kept for troubleshooting and benchmarking purposes.
        """
        queryset = self
        if search_term:
            search_term = search_term[:100]

        filter_kwargs = {}
        if multi_tenant_company:
            filter_kwargs['multi_tenant_company'] = multi_tenant_company

        if search_fields and search_term:

            is_literal = False
            if search_term.startswith('"') and search_term.endswith('"') and len(search_term) > 1:
                is_literal = True

            orm_lookups = self._build_orm_lookups(search_fields=search_fields, is_literal=is_literal)
            for bit in smart_split(search_term):
                if bit.startswith(('"', "'")) and bit[0] == bit[-1]:
                    bit = unescape_string_literal(bit)
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]

                queryset = queryset.filter(reduce(operator.or_, or_queries), **filter_kwargs)

            may_have_duplicates = self.lookup_needs_distinct(self, orm_lookups)
        else:
            may_have_duplicates = False

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

    def search_old(self, search_term, multi_tenant_company=None):
        if search_term:
            search_term = search_term[:100]
        try:
            search_fields = self.model._meta.search_terms
        except AttributeError:
            logger.warning("No `search_terms` declared on the model Meta class")
            search_fields = []

        qs, _ = self.get_search_results_old(
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

    def search_old(self, search_term, multi_tenant_company=None):
        return self.get_queryset().search_old(search_term=search_term, multi_tenant_company=multi_tenant_company)