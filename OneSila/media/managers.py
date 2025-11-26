from core.managers import QuerySet, Manager, MultiTenantCompanyCreateMixin, \
    QuerySetProxyModelMixin, MultiTenantQuerySet, MultiTenantManager
import base64
from hashlib import sha256
from django.core.files.base import ContentFile
from django.db import transaction, IntegrityError


class MediaQuerySet(MultiTenantQuerySet):
    pass


class MediaProductThroughQuerySet(MultiTenantQuerySet):
    def get_product_images(self, *, product, sales_channel=None):
        base_queryset = self.filter(product=product)

        if sales_channel is None:
            return base_queryset.filter(sales_channel__isnull=True)

        sales_channel_queryset = base_queryset.filter(sales_channel=sales_channel)

        if sales_channel_queryset.exists():
            return sales_channel_queryset

        return base_queryset.filter(sales_channel__isnull=True)


class MediaProductThroughManager(MultiTenantManager):
    def get_queryset(self):
        return MediaProductThroughQuerySet(self.model, using=self._db)

    def get_product_images(self, *, product, sales_channel=None):
        return self.get_queryset().get_product_images(product=product, sales_channel=sales_channel)


class MediaManager(MultiTenantManager):
    def get_queryset(self):
        return MediaQuerySet(self.model, using=self._db)

    @staticmethod
    def _decode_base64(image_raw_base64: bytes) -> bytes:
        """Decode a base64-encoded image."""
        return base64.decodebytes(image_raw_base64)

    @staticmethod
    def _hash_string(image_decoded: bytes) -> str:
        """Return the sha256 hex digest for the given bytes."""
        return sha256(image_decoded).hexdigest()

    def _compute_hash_from_file(self, image_file) -> tuple[str, bytes]:
        """
        Compute the SHA-256 hash of the file's content.
        Returns a tuple (hash, content).
        """
        # Ensure we start reading at the beginning
        image_file.seek(0)
        content = image_file.read()
        # Optionally, if you need to mimic a base64 conversion:
        # image_base64 = base64.encodebytes(content)
        # hash_value = sha256(image_base64).hexdigest()
        hash_value = sha256(content).hexdigest()
        return hash_value, content

    @transaction.atomic
    def create(self, *args, **kwargs):
        """
        Overrides create() so that if we're creating an image (i.e. type is IMAGE)
        and an image file is provided, we compute its hash and check for an existing record.
        Otherwise, we fall back to the normal create behavior.
        """

        # Only apply deduplication if we're dealing with an image.
        if kwargs.get('type') != self.model.IMAGE or 'image' not in kwargs:
            return super().create(*args, **kwargs)

        # Pop the image file (an UploadedFile or similar) from kwargs.
        image_file = kwargs.pop('image')
        image_hash, content = self._compute_hash_from_file(image_file)

        # Use multi_tenant_company (not owner) as our context.
        multi_tenant_company = kwargs.get('multi_tenant_company')
        if not multi_tenant_company:
            raise ValueError("multi_tenant_company is required for image creation")

        # Check for an existing instance with the same hash and multi_tenant_company.
        try:
            instance = self.get(image_hash=image_hash, multi_tenant_company=multi_tenant_company)
            return instance
        except self.model.DoesNotExist:
            # No duplicate found – prepare to create a new instance.
            image_name = kwargs.pop('image_name', 'image.png')
            kwargs['image_hash'] = image_hash
            instance = self.model(**kwargs)
            # Save the image file using our file content.
            instance.image.save(image_name, ContentFile(content), save=False)
            try:
                instance.save()
                return instance
            except IntegrityError:
                # Another process created the same image concurrently
                return self.get(image_hash=image_hash, multi_tenant_company=multi_tenant_company)

    @transaction.atomic
    def get_or_create(self, defaults=None, **kwargs):
        """
        Overrides get_or_create() to apply deduplication for image creation.
        If the type is not IMAGE or an image file isn’t provided, falls back to super().
        """
        if kwargs.get('type') != self.model.IMAGE or 'image' not in kwargs:
            return super().get_or_create(defaults=defaults, **kwargs)

        image_file = kwargs.pop('image')
        image_hash, content = self._compute_hash_from_file(image_file)

        multi_tenant_company = kwargs.get('multi_tenant_company')
        if not multi_tenant_company:
            raise ValueError("multi_tenant_company is required for image creation")

        try:
            instance = self.get(image_hash=image_hash, multi_tenant_company=multi_tenant_company)
            return instance, False
        except self.model.DoesNotExist:
            image_name = kwargs.pop('image_name', 'image.png')
            kwargs['image_hash'] = image_hash
            instance = self.model(**kwargs)
            instance.image.save(image_name, ContentFile(content), save=False)
            try:
                instance.save()
                created = True
            except IntegrityError:
                # Another process inserted the image in parallel
                instance = self.get(image_hash=image_hash, multi_tenant_company=multi_tenant_company)
                created = False
            return instance, created


class ImageQuerySet(MediaQuerySet, QuerySetProxyModelMixin):
    pass


class ImageManager(MediaManager):
    def get_queryset(self):
        return ImageQuerySet(self.model, using=self._db)

    def create(self, *args, **kwargs):
        kwargs.setdefault('type', self.model.IMAGE)
        return super().create(*args, **kwargs)

    def get_or_create(self, defaults=None, **kwargs):
        kwargs.setdefault("type", self.model.IMAGE)

        # prevent accidental override from defaults
        if defaults and "type" in defaults and defaults["type"] != self.model.IMAGE:
            defaults = dict(defaults)
            defaults["type"] = self.model.IMAGE
        return super().get_or_create(defaults=defaults, **kwargs)

class VideoQuerySet(MediaQuerySet, QuerySetProxyModelMixin):
    pass


class VideoManager(MediaManager):
    def get_queryset(self):
        return VideoQuerySet(self.model, using=self._db)

    def create(self, *args, **kwargs):
        kwargs.setdefault('type', self.model.VIDEO)
        return super().create(*args, **kwargs)

    def get_or_create(self, defaults=None, **kwargs):
        kwargs.setdefault("type", self.model.VIDEO)
        # prevent accidental override from defaults
        if defaults and "type" in defaults and defaults["type"] != self.model.VIDEO:
            defaults = dict(defaults)
            defaults["type"] = self.model.VIDEO
        return super().get_or_create(defaults=defaults, **kwargs)


class FileQuerySet(MediaQuerySet, QuerySetProxyModelMixin):
    pass


class FileManager(MediaManager):
    def get_queryset(self):
        return FileQuerySet(self.model, using=self._db)

    def create(self, *args, **kwargs):
        kwargs.setdefault('type', self.model.FILE)
        return super().create(*args, **kwargs)

    def get_or_create(self, defaults=None, **kwargs):
        kwargs.setdefault("type", self.model.FILE)
        # prevent accidental override from defaults
        if defaults and "type" in defaults and defaults["type"] != self.model.FILE:
            defaults = dict(defaults)
            defaults["type"] = self.model.FILE
        return super().get_or_create(defaults=defaults, **kwargs)
