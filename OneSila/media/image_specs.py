from imagekit import ImageSpec, register
from imagekit.processors import ResizeToFill, ResizeToFit
from imagekit.utils import get_field_info

import os


class OneSilaThumbnail(ImageSpec):
    processors = [ResizeToFill(560, 480)]
    format = 'JPEG'
    options = {'quality': 60}


class ImageWebSpec(ImageSpec):
    '''
    Image spec class to resize images with resizetofit.
    Resolution 1920x1080
    format jpeg
    quality 60

    biggest trade is the filename. It uses the original filename
    or an seo-name.  Not the default hash
    '''
    maximum_size = 250000   # Maximum filesize the generated image should have.

    def __init__(self, source):
        self.source = source
        self.determine_sizing()
        super(ImageSpec, self).__init__()

    def _set_settings(self, w, h, q):
        '''
        Set the width, height and quality
        '''
        self.processors = [ResizeToFit(w, h)]
        self.format = 'JPEG'
        self.options = {'quality': q}

    def determine_sizing(self):
        '''
        Guess the right resizing information based upon the source-size
        '''

        # TODO implement 'is_landscape' and set correct sizing for landscape and portrait

        try:
            source_size = getattr(self.source, 'size', None)

            if source_size >= 22000000:
                self._set_settings(1024, 900, 60)
            elif source_size >= 15000000:
                self._set_settings(1280, 1024, 70)
            elif source_size >= 11000000:
                self._set_settings(1920, 1080, 70)
            else:
                self._set_settings(1920, 1080, 70)
        except ValueError:  # sometimes there isnt a file known.  Set default values.
            self._set_settings(1920, 1080, 70)

    # Standard mode is to hash the image names.  However, this is bad SEO
    # so we will use the product name.
    @property
    def cachefile_name(self):
        source_filename = getattr(self.source, 'name', None)
        source_base, _ = os.path.split(source_filename)
        _, source_extension = os.path.splitext(source_filename)

        base_folder = os.path.join('CACHE', 'image_web', source_base)

        model, field_name = get_field_info(self.source)

        product_name = model.seo_name
        if product_name:
            filename = '{}{}'.format(product_name, source_extension)
        else:
            filename = source_filename

        return os.path.join(base_folder, filename)


register.generator('mediapp:image:imagewebspec', ImageWebSpec)
register.generator('mediapp:image:onesilathumbnail', OneSilaThumbnail)


class SheinMainImageSpec(ImageSpec):
    processors = [ResizeToFill(1340, 1785)]
    format = 'JPEG'
    options = {'quality': 85}
    maximum_size = 3_000_000


class SheinDetailImageSpec(ImageSpec):
    processors = [ResizeToFill(1340, 1785)]
    format = 'JPEG'
    options = {'quality': 85}
    maximum_size = 3_000_000


class SheinSquareImageSpec(ImageSpec):
    processors = [ResizeToFill(900, 900)]
    format = 'JPEG'
    options = {'quality': 85}
    maximum_size = 3_000_000


class SheinColorBlockImageSpec(ImageSpec):
    processors = [ResizeToFill(80, 80)]
    format = 'JPEG'
    options = {'quality': 85}
    maximum_size = 3_000_000


class SheinDetailPageImageSpec(ImageSpec):
    processors = [ResizeToFill(900, 1200)]
    format = 'JPEG'
    options = {'quality': 85}
    maximum_size = 3_000_000


register.generator('mediapp:image:sheinmain', SheinMainImageSpec)
register.generator('mediapp:image:sheindetail', SheinDetailImageSpec)
register.generator('mediapp:image:sheinsquare', SheinSquareImageSpec)
register.generator('mediapp:image:sheincolorblock', SheinColorBlockImageSpec)
register.generator('mediapp:image:sheindetailpage', SheinDetailPageImageSpec)
