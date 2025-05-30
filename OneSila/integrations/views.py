from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseForbidden

from core.views import EmptyTemplateView
from .models import IntegrationTaskQueue


@login_required
@user_passes_test(lambda u: u.is_superuser)
def retry_integration_task(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(IntegrationTaskQueue, id=task_id)
        task.retry_task(retry_now=True)
        messages.success(request, f"Task {task.name} has been retried.")
    else:
        return HttpResponseForbidden("Invalid request method.")

    return redirect(request.META.get('HTTP_REFERER', '/'))


class IntegrationListView(EmptyTemplateView):
    pass


class ShopifyIntegrationDetailView(EmptyTemplateView):
    pass
