import logging

from django.dispatch import receiver

from core.models.multi_tenant import MultiTenantUser
from core.signals import multi_tenant_company_created
from telegram_bot.factories import TelegramAdminNotificationFactory

logger = logging.getLogger(__name__)


@receiver(multi_tenant_company_created, sender=MultiTenantUser)
def telegram_bot__multi_tenant_user__notify_admins(*, sender, instance, **kwargs):
    if not instance:
        return

    factory = TelegramAdminNotificationFactory(user=instance)
    try:
        factory.run()
    except Exception:
        logger.exception("Failed to dispatch Telegram notifications for %s", instance)
