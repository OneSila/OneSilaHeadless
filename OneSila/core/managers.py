from django.db.models import QuerySet as DjangoQueryset
from django.db.models import Manager as DjangoManager
from django.db import IntegrityError
from django.db.models import QuerySet

from django.contrib.auth.models import BaseUserManager


class MultiTenantQuerySet(DjangoQueryset):
    def filter(self, *, multi_tenant_company, **kwargs):
        return super().filter(multi_tenant_company=multi_tenant_company, **kwargs)


class MultiTenantManager(DjangoManager):
    def get_queryset(self):
        return MultiTenantQuerySet(self.model, using=self._db)

    def create(self, *, multi_tenant_company, **kwargs):
        return super().create(multi_tenant_company=multi_tenant_company, **kwargs)

    def get_or_create(self, *, multi_tenant_company, **kwargs):
        return super().get_or_create(multi_tenant_company=multi_tenant_company, **kwargs)


class MultiTenantUserManager(BaseUserManager):
    """
    A custom user manager to deal with emails as unique identifiers for auth
    instead of usernames. The default that's used is "UserManager"
    """

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class MultiTenantCompanyCreateMixin:
    def create(self, *args, **kwargs):
        multi_tenant_company = kwargs.get('multi_tenant_company')

        if not multi_tenant_company:
            raise IntegrityError("You cannot create without setting a multi_tenant_company value.")

        return super().create(*args, **kwargs)


class Manager(DjangoManager):
    def get_queryset(self):
        return QuerySet(self.model, using=self._db)


class QuerySetProxyModelMixin:
    """
    Should you wish ot use this mixin for proxy-classes, dont forget to set
    - proxy_filter_field on the model
    """

    def filter(self, *args, **kwargs):
        kwargs.update(self.model.proxy_filter_field)
        return super().filter(*args, **kwargs)

    def create(self, **kwargs):
        kwargs.update(self.model.proxy_filter_field)
        return super().create(**kwargs)

    def all(self):
        return self.filter()
