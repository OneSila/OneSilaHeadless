import logging
from typing import Iterable, List

from asgiref.sync import async_to_sync
from django.conf import settings

from core.models.multi_tenant import MultiTenantUser
from telegram_bot.bot import notify_new_user_creation
from telegram_bot.models import TelegramUser

logger = logging.getLogger(__name__)


class TelegramAdminNotificationFactory:
    """
    Sends Telegram notifications to platform administrators when a new user registers.
    """

    def __init__(self, *, user: MultiTenantUser):
        self.user = user

    def run(self):
        admin_usernames = self._admin_usernames()
        if not admin_usernames:
            return

        telegram_users = self._get_target_telegram_users(admin_usernames)
        if not telegram_users:
            return

        self._notify_targets(telegram_users)

    def _admin_usernames(self) -> List[str]:
        admin_pairs = getattr(settings, "ADMINS", None) or []
        return [email for _, email in admin_pairs if email]

    def _get_target_telegram_users(self, admin_usernames: Iterable[str]) -> List[TelegramUser]:
        return list(TelegramUser.objects.filter(user__username__in=admin_usernames))

    def _notify_targets(self, telegram_users: Iterable[TelegramUser]):
        notifier = async_to_sync(notify_new_user_creation)
        for telegram_user in telegram_users:
            chat_id = telegram_user.chat_id or telegram_user.telegram_user_id
            if not chat_id:
                logger.warning(
                    "Telegram user %s has no chat id; skipping notification", telegram_user.telegram_user_id
                )
                continue

            try:
                notifier(chat_id=str(chat_id), user=self.user)
            except Exception:
                logger.exception(
                    "Failed to send Telegram notification for chat_id %s", chat_id
                )
