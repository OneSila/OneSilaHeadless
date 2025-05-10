from media.models import Image, MediaProductThrough
import os
from django.conf import settings
from model_bakery import baker
from django.core.files import File


class CreateImageMixin:
    def create_image(self, multi_tenant_company, fname='red.png'):
        image_path = os.path.join(settings.BASE_DIR.parent, 'core', 'tests', 'image_files', fname)
        image = baker.make(Image, multi_tenant_company=multi_tenant_company)

        with open(image_path, 'rb') as f:
            image.image.save(fname, File(f))
            image.full_clean()
            image.save()
            return image

    def create_and_attach_image(self, product, fname='red.png'):
        image = self.create_image(product.multi_tenant_company, fname)
        MediaProductThrough.objects.create(product=product, media=image, multi_tenant_company=product.multi_tenant_company)
        return image
