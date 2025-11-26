from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

hostname_validator = RegexValidator(
    regex=r'^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$',
    message=_('Enter a valid hostname (e.g., example.com)')
)