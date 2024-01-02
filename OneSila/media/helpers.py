import os

import logging
logger = logging.getLogger(__name__)


def sanitize_media_filename(filename):
    '''
    1) Get rid of dots and replace by understore
    2) lowercase extension
    '''
    filename_split = filename.split('.')
    filename = '{}.{}'.format('_'.join(filename_split[:-1]), filename_split[-1].lower())

    return filename


def is_landscape(w, h):
    '''
    Returns True if image is landscape
    '''
    return (w / h) > 1
