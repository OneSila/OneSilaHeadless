from core.managers import QuerySet, Manager, MultiTenantCompanyCreateMixin, \
    QuerySetProxyModelMixin, MultiTenantQuerySet, MultiTenantManager


class MediaQuerySet(MultiTenantQuerySet):
    pass


class MediaManager(MultiTenantManager):
    def get_queryset(self):
        return MediaQuerySet(self.model, using=self._db)


class ImageQuerySet(MediaQuerySet, QuerySetProxyModelMixin):
    pass


class ImageManager(MediaManager):
    def get_queryset(self):
        return ImageQuerySet(self.model, using=self._db)

    def create(self, *args, **kwargs):
        kwargs.setdefault('type', self.model.IMAGE)
        return super().create(*args, **kwargs)


class VideoQuerySet(MediaQuerySet, QuerySetProxyModelMixin):
    pass


class VideoManager(MediaManager):
    def get_queryset(self):
        return VideoQuerySet(self.model, using=self._db)

    def create(self, *args, **kwargs):
        kwargs.setdefault('type', self.model.VIDEO)
        return super().create(*args, **kwargs)


class FileQuerySet(MediaQuerySet, QuerySetProxyModelMixin):
    pass


class FileManager(MediaManager):
    def get_queryset(self):
        return FileQuerySet(self.model, using=self._db)

    def create(self, *args, **kwargs):
        kwargs.setdefault('type', self.model.FILE)
        return super().create(*args, **kwargs)
