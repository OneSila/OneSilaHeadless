from django.conf import settings
from get_absolute_url.helpers import reverse_lazy


def get_languages():
    return settings.LANGUAGES
