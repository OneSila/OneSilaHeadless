from django.db.models import *
from django.db import IntegrityError
from django.db.models import Model as OldModel
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.conf import settings

from .validators import phone_regex
from .managers import MultiTenantUserManager


def get_languages():
    return settings.LANGUAGES


class MultiTenantCompany(OldModel):
    '''
    Class that holds company information and sales-conditions.
    '''
    from .countries import COUNTRY_CHOICES
    LANGUAGE_CHOICES = get_languages()

    name = CharField(max_length=100)
    address1 = CharField(max_length=100, null=True, blank=True)
    address2 = CharField(max_length=100, null=True, blank=True)
    postcode = CharField(max_length=100, null=True, blank=True)
    city = CharField(max_length=100, null=True, blank=True)
    country = CharField(max_length=3, choices=COUNTRY_CHOICES, null=True, blank=True)
    language = CharField(max_length=7, choices=LANGUAGE_CHOICES, default=settings.LANGUAGE_CODE)

    email = EmailField(blank=True, null=True)
    phone_number = CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    vat_number = CharField(max_length=30, null=True, blank=True)
    website = URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = _("Multi tenant companies")


class MultiTenantAwareMixin(OldModel):
    multi_tenant_company = ForeignKey(MultiTenantCompany, on_delete=PROTECT, null=True, blank=True)

    class Meta:
        abstract = True


class MultiTenantMultiAwareMixin(OldModel):
    multi_tenant_company = ManyToManyField(MultiTenantCompany)

    class Meta:
        abstract = True


class MultiTenantUser(AbstractUser, MultiTenantAwareMixin):
    '''
    Q: Why is this user-class abusing the username as an email-field instead of just
    changing the class?
    A: Because starwberry-django will break and rewriting this field is not something
    that's in the cards today.
    '''
    username = EmailField(unique=True, help_text=_('Email Address'))

    def __str__(self):
        return f"{self.username} <{self.multi_tenant_company}>"

    def save(self, *args, **kwargs):
        self.email = self.username

        super().save(*args, **kwargs)

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


class TimeStampMixin(OldModel):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Model(TimeStampMixin, MultiTenantAwareMixin, OldModel):
    class Meta:
        abstract = True


class SharedModel(TimeStampMixin, OldModel):
    class Meta:
        abstract = True
