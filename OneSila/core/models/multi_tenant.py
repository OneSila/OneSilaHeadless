from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from core.validators import phone_regex, validate_image_extension, \
    no_dots_in_filename
from core.helpers import get_languages


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

    class Meta:
        verbose_name_plural = _("Multi tenant companies")


class MultiTenantAwareMixin(models.Model):
    multi_tenant_company = models.ForeignKey(MultiTenantCompany, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        abstract = True


class MultiTenantMultiAwareMixin(models.Model):
    multi_tenant_company = models.ManyToManyField(MultiTenantCompany)

    class Meta:
        abstract = True


class MultiTenantUser(AbstractUser, MultiTenantAwareMixin):
    '''
    Q: Why is this user-class abusing the username as an email-field instead of just
    changing the class?
    A: Because starwberry-django will break and rewriting this field is not something
    that's in the cards today.
    '''
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
    avatar = models.ImageField(upload_to='avatars', null=True,
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
