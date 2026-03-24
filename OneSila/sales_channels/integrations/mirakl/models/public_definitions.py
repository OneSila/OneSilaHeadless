from core import models

from .properties import MiraklProperty


class MiraklPublicDefinition(models.SharedModel):
    hostname = models.CharField(max_length=255)
    property_code = models.CharField(max_length=255)
    representation_type = models.CharField(
        max_length=64,
        choices=MiraklProperty.REPRESENTATION_TYPE_CHOICES,
        default=MiraklProperty.REPRESENTATION_PROPERTY,
    )
    language = models.CharField(max_length=64, null=True, blank=True, default=None)
    default_value = models.CharField(max_length=255, blank=True, default="")
    yes_text_value = models.CharField(max_length=255, blank=True, default="")
    no_text_value = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "Mirakl Public Definition"
        verbose_name_plural = "Mirakl Public Definitions"
        constraints = [
            models.UniqueConstraint(
                fields=["hostname", "property_code"],
                name="unique_mirakl_public_definition_per_host_property",
            ),
        ]
        search_terms = ["hostname", "property_code", "representation_type"]

    def __str__(self) -> str:
        return f"[{self.hostname}] {self.property_code}"
