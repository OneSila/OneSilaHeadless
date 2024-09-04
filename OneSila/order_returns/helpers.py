import os

import logging
logger = logging.getLogger(__name__)


def get_orderreturn_attachment_folder_upload_path(instance, filename):
    '''Return a dynmic path based on the selection location.  And clean the filename'''
    path = os.path.join('order_returns', str(instance.pk), 'attachment_files', filename)

    logger.debug("Upload path {}".format(path))

    return path
