from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import shutil


from telegram_bot.bot import bot, Update

class Command(BaseCommand):
    help = ("Run the telegram bot poll")

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        bot.run_polling(allowed_updates=Update.ALL_TYPES)
