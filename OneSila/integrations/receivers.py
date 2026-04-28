import logging

from core.receivers import receiver
from core.signals import post_create
from integrations.models import PublicIssue, PublicIssueRequest
from telegram_bot.factories import TelegramAdminNotificationFactory

logger = logging.getLogger(__name__)

# @receiver(post_update, sender='app_name.Model')
# def app_name__model__action__example(sender, instance, **kwargs):
#     do_something()


@receiver(post_create, sender=PublicIssueRequest)
def integrations__public_issue_request__post_create__notify_admins(*, sender, instance, **kwargs):
    if not instance:
        return

    try:
        factory = TelegramAdminNotificationFactory(public_issue_request=instance)
        factory.run()
    except Exception:
        logger.exception("Failed to dispatch Telegram notifications for %s", instance)


@receiver(post_create, sender=PublicIssue)
def integrations__public_issue__post_create__accept_public_issue_request(*, sender, instance, **kwargs):
    if not instance or not instance.request_reference:
        return

    PublicIssueRequest.objects.filter(pk=instance.request_reference).update(status=PublicIssueRequest.ACCEPTED)
