from django.urls import path
from . import views

app_name = 'sales_channels'

urlpatterns = [
    path('retry_task/<int:task_id>/', views.retry_remote_task, name='retry_remote_task'),
]
