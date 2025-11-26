from django.contrib import admin

from telegram_bot.models import TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ("telegram_user_id", "chat_id", "user")
    search_fields = ("telegram_user_id", "chat_id", "user__username")
    raw_id_fields = ("user",)
