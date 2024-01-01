from django.db.models import QuerySet as DjangoQueryset
from django.db.models import Manager as DjangoManager
from core.managers.search import SearchQuerySetMixin, SearchManagerMixin


class QuerySet(SearchQuerySetMixin, DjangoQueryset):
    pass


class Manager(SearchManagerMixin, DjangoManager):
    def get_queryset(self):
        return QuerySet(self.model, using=self._db)
