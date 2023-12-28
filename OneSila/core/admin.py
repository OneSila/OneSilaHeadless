from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import MultiTenantCompany, MultiTenantUser
from .models.multi_tenant import MultiTenantUserLoginToken


@admin.register(MultiTenantUser)
class MultiTenantUserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'multi_tenant_company')}),
        (_('Profile info'), {'fields': ('language', 'avatar', 'mobile_number', 'whatsapp_number', 'telegram_number', 'timezone')}),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'is_multi_tenant_company_owner',
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
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    ordering = ('username',)
    search_fields = ('first_name', 'last_name', 'email')


@admin.register(MultiTenantCompany)
class MultiTenantCompanyAdmin(admin.ModelAdmin):
    pass

@admin.register(MultiTenantUserLoginToken)
class MultiTenantUserLoginTokenAdmin(admin.ModelAdmin):
    pass
