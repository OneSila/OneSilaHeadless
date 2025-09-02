from django.contrib import admin as django_admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import MultiTenantCompany, MultiTenantUser
from .models.multi_tenant import MultiTenantUserLoginToken


@django_admin.register(MultiTenantUser)
class MultiTenantUserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'multi_tenant_company')}),
        (_('Profile info'), {'fields': ('language', 'avatar', 'mobile_number', 'whatsapp_number', 'telegram_number', 'timezone')}),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'invitation_accepted', 'is_multi_tenant_company_owner', 'onboarding_status',
                'groups', 'user_permissions'
            ),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('username', 'multi_tenant_company', 'is_active')
    ordering = ('username',)
    search_fields = ('first_name', 'last_name', 'email')
    readonly_fields = ('multi_tenant_company',)


@django_admin.register(MultiTenantCompany)
class MultiTenantCompanyAdmin(django_admin.ModelAdmin):
    readonly_fields = ('created_at', 'updated_at')
    list_display = ('name', 'active')
    ordering = ('name',)
    search_fields = ('name',)
    list_filter = ('active',)
    date_hierarchy = 'created_at'


@django_admin.register(MultiTenantUserLoginToken)
class MultiTenantUserLoginTokenAdmin(django_admin.ModelAdmin):
    pass


class ModelAdmin(django_admin.ModelAdmin):
    raw_id_fields = [
        'multi_tenant_company',
        'created_by_multi_tenant_user',
        # 'last_updated_by_multi_tenant_user',
    ]


class SharedModelAdmin(django_admin.ModelAdmin):
    pass
