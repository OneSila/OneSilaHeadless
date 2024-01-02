from datetime import datetime
from functools import wraps
from django.core.exceptions import ValidationError


def multi_tenant_company_required():
    '''
    Ensure the multi-tentant-company is supplied in the kwargs or raise an ValidationError
    '''
    def deco_wrap(f):

        @wraps(f)
        def f_deco(*args, **kwargs):
            print(kwargs)
            multi_tenant_company = kwargs.get('multi_tenant_company')

            if not multi_tenant_company:
                raise ValidationError("You must supply a multi_tenant_company instance.")

            fn = f(*args, **kwargs)
            return fn

        return f_deco

    return deco_wrap
