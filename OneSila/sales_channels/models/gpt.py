from typing import Optional

from core import models
from get_absolute_url.helpers import generate_absolute_url


class SalesChannelGptFeed(models.Model):
    sales_channel = models.OneToOneField(
        'sales_channels.SalesChannel',
        on_delete=models.CASCADE,
        related_name='gpt_feed_record',
    )
    items = models.JSONField(
        default=list,
        blank=True,
        help_text="Cached GPT product feed entries for this sales channel.",
    )
    file = models.FileField(
        upload_to='gpt_feeds/',
        null=True,
        blank=True,
        help_text="Downloadable JSON file containing the GPT product feed.",
    )
    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the GPT feed was last synchronised.",
    )

    class Meta:
        verbose_name = 'Sales Channel GPT Feed'
        verbose_name_plural = 'Sales Channel GPT Feeds'

    def __str__(self) -> str:
        return f"GPT feed for {self.sales_channel}"

    @property
    def file_url(self) -> Optional[str]:
        if not self.file:
            return None
        try:
            return f"{generate_absolute_url(trailing_slash=False)}{self.file.url}"
        except ValueError:
            return None
