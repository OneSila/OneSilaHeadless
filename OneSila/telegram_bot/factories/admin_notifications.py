import logging
from typing import TYPE_CHECKING, Callable, Dict, Iterable, List, Tuple

from asgiref.sync import async_to_sync
from django.conf import settings

from core.models.multi_tenant import MultiTenantUser
from telegram_bot.bot import notify_new_user_creation, notify_public_issue_request_created
from telegram_bot.models import TelegramUser

if TYPE_CHECKING:
    from integrations.models import PublicIssueRequest

logger = logging.getLogger(__name__)


class TelegramAdminNotificationFactory:
    """
    Sends Telegram notifications to platform administrators.
    """

    def __init__(self, *, user: MultiTenantUser = None, public_issue_request: "PublicIssueRequest" = None):
        self.user = user
        self.public_issue_request = public_issue_request
        self._validate_payload()

    def run(self):
        admin_usernames = self._admin_usernames()
        if not admin_usernames:
            return

        telegram_users = self._get_target_telegram_users(admin_usernames)
        if not telegram_users:
            return

        self._notify_targets(telegram_users)

    def _validate_payload(self):
        payloads = [self.user, self.public_issue_request]
        if len([payload for payload in payloads if payload is not None]) != 1:
            raise ValueError("Provide exactly one Telegram admin notification payload.")

    def _admin_usernames(self) -> List[str]:
        admin_pairs = getattr(settings, "ADMINS", None) or []
        return [email for _, email in admin_pairs if email]

    def _get_target_telegram_users(self, admin_usernames: Iterable[str]) -> List[TelegramUser]:
        return list(TelegramUser.objects.filter(user__username__in=admin_usernames))

    def _notification_payload(self) -> Tuple[Callable, Dict[str, object], str]:
        if self.user:
            return notify_new_user_creation, {"user": self.user}, str(self.user)

        return (
            notify_public_issue_request_created,
            {"public_issue_request": self.public_issue_request},
            str(self.public_issue_request),
        )

    def _notify_targets(self, telegram_users: Iterable[TelegramUser]):
        notification, payload, log_label = self._notification_payload()
        notifier = async_to_sync(notification)
        for telegram_user in telegram_users:
            chat_id = telegram_user.chat_id or telegram_user.telegram_user_id
            if not chat_id:
                logger.warning(
                    "Telegram user %s has no chat id; skipping notification", telegram_user.telegram_user_id
                )
                continue

            try:
                notifier(chat_id=str(chat_id), **payload)
            except Exception:
                logger.exception(
                    "Failed to send Telegram notification for %s to chat_id %s", log_label, chat_id
                )
