from imagekit import ImageSpec, register
from imagekit.processors import ResizeToFill, ResizeToFit
from imagekit.utils import get_field_info

import os
from typing import Optional, Tuple


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


class _DynamicSheinImageSpec(ImageSpec):
    format = 'JPEG'
    options = {'quality': 85}
    maximum_size = 3_000_000

    def __init__(self, source):
        self.source = source
        self.processors = [self._build_processor()]
        super().__init__(source)

    def _build_processor(self):
        raise NotImplementedError("Subclasses must implement _build_processor().")

    @staticmethod
    def _clamp(value, minimum, maximum):
        return max(minimum, min(int(round(value)), maximum))

    def _source_dimensions(self) -> Tuple[Optional[int], Optional[int]]:
        width = getattr(self.source, 'width', None)
        height = getattr(self.source, 'height', None)
        if width and height:
            return int(width), int(height)

        name = getattr(self.source, 'name', None)
        storage = getattr(self.source, 'storage', None)
        if not name or storage is None:
            return None, None

        try:
            from PIL import Image as PILImage

            with storage.open(name, 'rb') as fh:
                with PILImage.open(fh) as image:
                    return int(image.width), int(image.height)
        except Exception:
            return None, None

    def _square_fit_processor(self, *, width, height, min_side=900, max_side=2200):
        side = max(width, height)
        side = self._clamp(side, min_side, max_side)
        return ResizeToFit(side, side, upscale=True, mat_color='white')


class _DynamicSheinMainDetailSpec(_DynamicSheinImageSpec):
    _PORTRAIT_WIDTH = 1340
    _PORTRAIT_HEIGHT = 1785
    _PORTRAIT_RATIO = _PORTRAIT_WIDTH / _PORTRAIT_HEIGHT

    def _build_processor(self):
        width, height = self._source_dimensions()
        if not width or not height:
            return ResizeToFit(
                self._PORTRAIT_WIDTH,
                self._PORTRAIT_HEIGHT,
                upscale=True,
                mat_color='white',
            )

        source_ratio = width / height
        distance_square = abs(source_ratio - 1.0)
        distance_portrait = abs(source_ratio - self._PORTRAIT_RATIO)

        if distance_square <= distance_portrait:
            return self._square_fit_processor(width=width, height=height)

        return ResizeToFit(
            self._PORTRAIT_WIDTH,
            self._PORTRAIT_HEIGHT,
            upscale=True,
            mat_color='white',
        )


class SheinMainImageSpec(_DynamicSheinMainDetailSpec):
    pass


class SheinDetailImageSpec(_DynamicSheinMainDetailSpec):
    pass


class SheinSquareImageSpec(_DynamicSheinImageSpec):
    def _build_processor(self):
        width, height = self._source_dimensions()
        if not width or not height:
            return ResizeToFit(900, 900, upscale=True, mat_color='white')

        is_square = width == height
        if is_square and 900 <= width <= 2200:
            # Keep already-compliant square dimensions as-is.
            return ResizeToFit(width, height, upscale=False)

        return self._square_fit_processor(width=width, height=height)


class SheinColorBlockImageSpec(ImageSpec):
    processors = [ResizeToFill(80, 80)]
    format = 'JPEG'
    options = {'quality': 85}
    maximum_size = 3_000_000


class SheinDetailPageImageSpec(_DynamicSheinImageSpec):
    _RATIO = 3 / 4
    _MIN_WIDTH = 900
    _MAX_WIDTH = 2200
    _MIN_HEIGHT = 1200

    def _build_processor(self):
        width, height = self._source_dimensions()
        if not width or not height:
            return ResizeToFit(900, 1200, upscale=True, mat_color='white')

        target_width = self._clamp(width, self._MIN_WIDTH, self._MAX_WIDTH)
        target_height = int(round(target_width / self._RATIO))

        if target_height < self._MIN_HEIGHT:
            target_height = self._MIN_HEIGHT
            target_width = int(round(target_height * self._RATIO))

        return ResizeToFit(target_width, target_height, upscale=True, mat_color='white')


register.generator('mediapp:image:sheinmain', SheinMainImageSpec)
register.generator('mediapp:image:sheindetail', SheinDetailImageSpec)
register.generator('mediapp:image:sheinsquare', SheinSquareImageSpec)
register.generator('mediapp:image:sheincolorblock', SheinColorBlockImageSpec)
register.generator('mediapp:image:sheindetailpage', SheinDetailPageImageSpec)
