import os

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


def validate_image_extension(value):
    '''Validate if the upload has is a jpg or png image'''
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_('Only {} are allowed.'.format(valid_extensions)))


def no_dots_in_filename(value):
    ''' validate is a filename doesnt contain any dots'''
    split = value.name.split('.')
    if len(split) > 2:
        raise ValidationError(_('No dots are allowed in the filename'))
