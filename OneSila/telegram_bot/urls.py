from django.urls import path
from .views import start_bot, stop_bot

urlpatterns = [
    path("start/", start_bot, name="start_bot"),
    path("stop/", stop_bot, name="stop_bot"),
]
