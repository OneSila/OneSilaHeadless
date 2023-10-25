from django.middleware.csrf import CsrfViewMiddleware


class DisableCSRF(CsrfViewMiddleware):
    '''
    Disable CSRF
    https://stackoverflow.com/a/4631626/5731101
    https://docs.djangoproject.com/en/3.2/topics/http/middleware/
    https://github.com/django/django/blob/main/django/middleware/csrf.py
    '''

    def process_request(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)
