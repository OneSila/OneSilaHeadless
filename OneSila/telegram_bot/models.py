from django.db import models
from django.utils.translation import gettext_lazy as _


class TelegramUser(models.Model):
    user = models.ForeignKey(
        'core.MultiTenantUser',
        on_delete=models.CASCADE,
        related_name='telegram_users',
        blank=True,
        null=True,
    )
    telegram_user_id = models.CharField(_('user id'), max_length=100, unique=True)
    chat_id = models.CharField(
        _('chat id'),
        max_length=100,
        help_text=_('Chat id is the same as user id'),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.telegram_user_id

    def set_chat_id(self, *, save=False):
        if not self.chat_id:
            self.chat_id = self.telegram_user_id

        if save:
            self.save(update_fields=['chat_id'])

    def save(self, *args, **kwargs):
        self.set_chat_id(save=False)
        super().save(*args, **kwargs)
