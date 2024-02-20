import os
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."))


def validate_image_extension(value):
    '''Validate if the upload has is a jpg or png image'''
    ext = os.path.splitext(value.name)[1]
    # Images are restricted to "validate_image_extension". Keep in mind if you want to extend this restriction
    # to also update the frontend, and extend the cropping tools so that no conflicts arise.
    valid_extensions = ['.jpg', '.png', '.jpeg']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_('Only {} are allowed.'.format(valid_extensions)))


def validate_file_extensions(value):
    ext = os.path.splitext(value.name)[1]
    # Images are restricted to "validate_image_extension". Keep in mind if you want to extend this restriction
    # to also update the frontend, and extend the cropping tools so that no conflicts arise.
    valid_extensions = ['.pdf', '.xlsx', '.xls', '.docx', '.doc']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_('Only {} are allowed.'.format(valid_extensions)))


def no_dots_in_filename(value):
    ''' validate is a filename doesnt contain any dots'''
    split = value.name.split('.')
    if len(split) > 2:
        raise ValidationError(_('No dots are allowed in the filename'))
