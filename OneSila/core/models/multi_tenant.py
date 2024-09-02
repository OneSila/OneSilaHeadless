from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language_info


from core.validators import phone_regex
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from imagekit.exceptions import MissingSource

from core.typing import LanguageType, TimezoneType
from core.helpers import get_languages
from core.managers import MultiTenantManager, MultiTenantUserLoginTokenManager
from core.validators import phone_regex, validate_image_extension, \
    no_dots_in_filename

from get_absolute_url.helpers import generate_absolute_url
from hashlib import shake_256
import shortuuid


class MultiTenantCompany(models.Model):
    '''
    Class that holds company information and sales-conditions.
    '''
    from core.countries import COUNTRY_CHOICES

    LANGUAGE_CHOICES = get_languages()

    name = models.CharField(max_length=100)
    address1 = models.CharField(max_length=100, null=True, blank=True)
    address2 = models.CharField(max_length=100, null=True, blank=True)
    postcode = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=3, choices=COUNTRY_CHOICES, null=True, blank=True)
    language = models.CharField(max_length=7, choices=LANGUAGE_CHOICES, default=settings.LANGUAGE_CODE)

    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    vat_number = models.CharField(max_length=30, null=True, blank=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    def language_detail(self):
        return LanguageType(**get_language_info(self.language))

    class Meta:
        verbose_name_plural = _("Multi tenant companies")


class MultiTenantAwareMixin(models.Model):
    multi_tenant_company = models.ForeignKey(MultiTenantCompany, on_delete=models.PROTECT, null=True, blank=True)
    created_by_multi_tenant_user = models.ForeignKey("core.MultiTenantUser", on_delete=models.PROTECT, null=True, blank=True,
        related_name='%(class)s_created_by_multi_tenant_user_set')
    last_update_by_multi_tenant_user = models.ForeignKey("core.MultiTenantUser", on_delete=models.PROTECT, null=True, blank=True,
        related_name='%(class)s_last_update_by_multi_tenant_user_set')

    objects = MultiTenantManager()

    class Meta:
        abstract = True


class MultiTenantMultiAwareMixin(models.Model):
    multi_tenant_company = models.ManyToManyField(MultiTenantCompany)

    objects = MultiTenantManager()

    class Meta:
        abstract = True


class MultiTenantUser(AbstractUser, MultiTenantAwareMixin):
    '''
    Q: Why is this user-class abusing the username as an email-field instead of just
    changing the class?
    A: Because starwberry-django will break and rewriting this field is not something
    that's in the cards today.
    '''
    from core.timezones import TIMEZONE_CHOICES, DEFAULT_TIMEZONE

    ADD_COMPANY = 'ADD_COMPANY'  # - add owner company + create internal company + internal company address out of it
    ADD_CURRENCY = 'ADD_CURRENCY'  # - add default currency
    CONFIRM_VAT_RATE = 'CONFIRM_VAT_RATE'  # - edit / create VAT Rate
    CREATE_INVENTORY_LOCATION = 'CREATE_INVENTORY_LOCATION'  # add inventory location (can be skipped)
    GENERATE_DEMO_DATA = 'GENERATE_DEMO_DATA'  # - Ask if want demo data
    DASHBOARD_CARDS_PRESENTATION = 'DASHBOARD_CARDS_PRESENTATION'  # Presentation of dashboard Tutorial Carads
    COMPLETE_DASHBOARD_CARDS = 'COMPLETE_DASHBOARD_CARDS'  # Dashboard cards still not completed
    DONE = 'DONE'  # Everything is done

    ONBOARDING_STATUS_CHOICES = (
        (GENERATE_DEMO_DATA, _('Generate Demo Data')),
        (ADD_COMPANY, _('Add Company')),
        (ADD_CURRENCY, _('Add Currency')),
        (CONFIRM_VAT_RATE, _('Confirm VAT Rate')),
        (CREATE_INVENTORY_LOCATION, _('Create Inventory Location')),
        (DASHBOARD_CARDS_PRESENTATION, _('Dashboard Cards Presentation')),
        (COMPLETE_DASHBOARD_CARDS, _('Complete Dashboard Cards')),
        (DONE, _('Done')),
    )

    LANGUAGE_CHOICES = get_languages()

    username = models.EmailField(unique=True, help_text=_('Email Address'))

    # When users are created, the first one to register from a company is
    # declared as the owner.
    is_multi_tenant_company_owner = models.BooleanField(default=False)
    # Subsequent users are invited, this gets marked as accepted when the
    # relevant mutation is run.
    invitation_accepted = models.BooleanField(default=False)

    # Profile data:
    language = models.CharField(max_length=7, choices=LANGUAGE_CHOICES, default=settings.LANGUAGE_CODE)
    timezone = models.CharField(max_length=35, choices=TIMEZONE_CHOICES, default=timezone.get_default_timezone().key)
    mobile_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    whatsapp_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    telegram_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    onboarding_status = models.CharField(max_length=30, choices=ONBOARDING_STATUS_CHOICES, default=ADD_COMPANY)

    avatar = models.ImageField(upload_to='avatars', null=True, blank=True,
        validators=[validate_image_extension, no_dots_in_filename])
    avatar_resized = ImageSpecField(source='avatar',
                            processors=[ResizeToFill(100, 100)],
                            format='JPEG',
                            options={'quality': 70})

    def __str__(self):
        return f"{self.username} <{self.multi_tenant_company}>"

    def save(self, *args, **kwargs):
        self.email = self.username
        super().save(*args, **kwargs)

    def avatar_resized_full_url(self):
        if self.avatar:
            return f"{generate_absolute_url(trailing_slash=False)}{self.avatar_resized.url}"

        return None

    def full_name(self):
        return ' '.join([i for i in [self.first_name, self.last_name] if i is not None])

    def language_detail(self):
        return LanguageType(**get_language_info(self.language))

    def timezone_detail(self):
        return TimezoneType(key=self.timezone)

    def set_active(self, save=True):
        self.is_active = True

        if save:
            self.save()

    def set_inactive(self, save=True):
        self.is_active = False

        if save:
            self.save()

    class Meta:
        verbose_name = _("Multi tenant user")
        verbose_name_plural = _("Multi tenant users")

    # class Meta(AbstractUser.Meta):
    #     constraints = [
    #         CheckConstraint(
    #             check=Q(is_superuser=False, is_staff=False) ^ Q(company=None),
    #             name='user_has_company_if_no_staff_admin',
    #             violation_error_message=_("Users need to have a company assign. Staff and Superusers cannot.")
    #         ),
    #     ]


class MultiTenantUserLoginToken(models.Model):
    """
    A user can login with a "magic link". This is used for logging in and
    resetting the password.  Or in other words account recovery.
    """
    EXPIRES_AFTER_MIN = settings.MULTI_TENANT_LOGIN_LINK_EXPIRES_AFTER_MIN

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True)
    token = models.CharField(max_length=20, unique=True)

    multi_tenant_user = models.ForeignKey(MultiTenantUser, on_delete=models.CASCADE)

    objects = MultiTenantUserLoginTokenManager()

    def save(self, *args, **kwargs):
        self.set_token()
        super().save(*args, **kwargs)
        self.set_expires_at()

    def set_token(self):
        if not self.token:
            self.token = shake_256(shortuuid.uuid().encode('utf-8')).hexdigest(10)

    def set_expires_at(self, expires_at=None):
        # This strange construction is to avoid a second save signal.
        # if expires_at is not None:
        if expires_at is None:
            expires_at = self.created_at + timezone.timedelta(minutes=self.EXPIRES_AFTER_MIN)

        self.__class__.objects.filter(id=self.id).update(expires_at=expires_at)

    def is_valid(self, now=timezone.now()):
        return self.expires_at >= now
