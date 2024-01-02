from django.db.models import QuerySet as DjangoQueryset
from django.db.models import Manager as DjangoManager
from django.contrib.auth.models import BaseUserManager
from django.db import IntegrityError
from core.managers.search import SearchQuerySetMixin, SearchManagerMixin
from core.managers.decorators import multi_tenant_company_required


class MultiTenantUserLoginTokenQuerySet(DjangoQueryset):
    def get_by_token(self, token):
        try:
            instance = self.get(token=token)
        except self.model.DoesNotExist:
            raise ValidationError('Unknown token')

        if not instance.is_valid:
            raise ValidationError('Token is no longer valid')

        return instance


class MultiTenantUserLoginTokenManager(DjangoManager):
    def get_queryset(self):
        return MultiTenantUserLoginTokenQuerySet(self.model, using=self._db)

    def get_by_token(self, token):
        return self.get_queryset().get_by_token(token)


class MultiTenantQuerySet(SearchQuerySetMixin, DjangoQueryset):
    def get_search_results(self, *, search_term, search_fields, multi_tenant_company):
        return super().get_search_results(
            search_term=search_term,
            search_fields=search_fields,
            multi_tenant_company=multi_tenant_company,
        )

    def search(self, search_term, multi_tenant_company=None):
        return super().search(search_term=search_term, multi_tenant_company=multi_tenant_company)

    # def filter(self, *args, **kwargs):
    #     return super().filter(*args, **kwargs)

    # def all(self, multi_tenant_company=None):
    #     if multi_tenant_company:
    #         return self.filter(multi_tenant_company=multi_tenant_company)

    #     return self.filter()


class MultiTenantManager(SearchManagerMixin, DjangoManager):
    def get_queryset(self):
        return MultiTenantQuerySet(self.model, using=self._db)

    @multi_tenant_company_required()
    def create(self, **kwargs):
        return self.get_queryset().create(**kwargs)

    @multi_tenant_company_required()
    def get_or_create(self, **kwargs):
        return self.get_queryset().get_or_create(**kwargs)

    def search(self, search_term, multi_tenant_company):
        return self.get_queryset().search(search_term=search_term, multi_tenant_company=multi_tenant_company)

    # def filter(self, *args, **kwargs):
    #     return self.get_queryset().filter(*args, **kwargs)

    # def all(self, multi_tenant_company=None):
    #     return self.get_queryset().all(multi_tenant_company=multi_tenant_company)


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


class QuerySetProxyModelMixin(MultiTenantQuerySet):
    """
    Should you wish ot use this mixin for proxy-classes, dont forget to set
    - proxy_filter_field on the model
    """

    # @multi_tenant_company_required()
    def filter(self, **kwargs):
        kwargs.update(self.model.proxy_filter_fields)
        return super().filter(**kwargs)

    @multi_tenant_company_required()
    def create(self, **kwargs):
        kwargs.update(self.model.proxy_filter_fields)
        return super().create(**kwargs)

    def all(self, multi_tenant_company):
        return self.filter(multi_tenant_company=multi_tenant_company)
