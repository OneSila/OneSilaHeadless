import os

import logging
logger = logging.getLogger(__name__)


def get_shippinglabel_folder_upload_path(instance, filename):
    '''Return a dynmic path based on the selection location.  And clean the filename'''
    path = os.path.join('shipping', str(instance.pk), 'shipping_labels', filename)

    logger.debug("Upload path {}".format(path))

    return path


def get_customs_document_folder_upload_path(instance, filename):
    '''Return a dynmic path based on the selection location.  And clean the filename'''
    path = os.path.join('shipping', str(instance.pk), 'customs_documents', filename)

    logger.debug("Upload path {}".format(path))

    return path
