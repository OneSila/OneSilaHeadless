from functools import wraps

from django.core.exceptions import PermissionDenied


def multi_tenant_owner_protection():
    '''
    Protect data ownership by verifying both:
    - data doesnt contain an override for multi_tenant_company
    - instance has the right multi_tenant_company
    '''
    def deco_f(f):

        @wraps(f)
        def wrap_f(self, info, instance, data=None):
            # If data contains a multi-tenant company someone may be trying to tamper.
            # Dont raise an error, just remove the key silently.
            if data:
                try:
                    del data['multi_tenant_company']
                except (KeyError, AttributeError):
                    pass

            # If the instance is not owned by the user, raise a permission-error.
            if not instance.multi_tenant_company == self.get_multi_tenant_company(info):
                raise PermissionDenied("A user can only update objects that they own.")

            kwargs = {
                'info': info,
                'instance': instance,
            }

            if data:
                kwargs['data'] = data

            return f(self, **kwargs)

        return wrap_f

    return deco_f
