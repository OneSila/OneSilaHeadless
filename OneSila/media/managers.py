from django.db.models import QuerySet, Manager


class ImageQuerySet(QuerySet):
    pass


class ImageManager(Manager):
    def get_queryset(self):
        return ImageQuerySet(self.model, using=self._db)

    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs, type=self.model.IMAGE)


class VideoQuerySet(QuerySet):
    pass


class VideoManager(Manager):
    def get_queryset(self):
        return VideoQuerySet(self.model, using=self._db)

    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs, type=self.model.VIDEO)
