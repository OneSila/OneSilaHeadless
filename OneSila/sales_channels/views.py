from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import RemoteTaskQueue

@login_required
@user_passes_test(lambda u: u.is_superuser)
def retry_remote_task(request, task_id):
    task = get_object_or_404(RemoteTaskQueue, id=task_id)
    task.retry_task(retry_now=True)
    messages.success(request, f"Task {task.name} has been retried.")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
