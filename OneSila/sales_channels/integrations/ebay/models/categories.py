from core import models
from sales_channels.integrations.ebay.managers import EbayCategoryManager


class EbayCategory(models.SharedModel):
    marketplace_default_tree_id = models.CharField(max_length=50, db_index=True)
    remote_id = models.CharField(max_length=50)
    name = models.CharField(max_length=512)

    objects = EbayCategoryManager()

    class Meta:
        unique_together = ("marketplace_default_tree_id", "remote_id")
        ordering = ("marketplace_default_tree_id", "name")
        search_terms = ['remote_id', 'name']

    def __str__(self) -> str:
        return f"{self.name} ({self.remote_id})"
