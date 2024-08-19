from django.conf import settings
import os
from get_absolute_url.helpers import reverse_lazy


def get_languages():
    return settings.LANGUAGES


def save_test_file(filename, file_contents):
    filepath = os.path.join(settings.SAVE_TEST_FILES_ROOT, filename)
    with open(filepath, 'wb') as f:
        f.write(file_contents)

    return filepath
