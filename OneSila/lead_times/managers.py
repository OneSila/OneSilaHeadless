from core.managers import MultiTenantQuerySet, MultiTenantManager


class LeadTimeQuerySet(MultiTenantQuerySet):
    def order_by_fastest(self):
        return self.order_by('unit', 'max_time', 'min_time')

    def filter_fastest(self, leadtimes):
        # In order to filter on fast, we need to order the
        # units.  Probably a numeric value is really what the right
        # way to go is. 1 is fast, 3 is slow.  Then we just need
        # to order by unit, max_time and min_time and grab the first one.
        if isinstance(leadtimes, list):
            leadtimes = self.model.objects.filter(id__in=leadtimes)

        return self.order_by_fastest().first()


class LeadTimeManager(MultiTenantManager):
    def get_queryset(self):
        return LeadTimeQuerySet(self.model, using=self._db)

    def filter_fastest(self, leadtimes):
        return self.get_queryset().filter_fastest(leadtimes)

    def order_by_fastest(self):
        return self.get_queryset().order_by_fastest()
