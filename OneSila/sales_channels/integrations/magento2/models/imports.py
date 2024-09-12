from core import models
from sales_channels.models.imports import ImportableModel


class MagentoAttributeSetImport(ImportableModel):
    """
    Model representing the import process for Magento Attribute Sets.
    """

    remote_attribute_set = models.ForeignKey(
        'magento2.MagentoAttributeSet',
        on_delete=models.CASCADE,
        help_text="The remote attribute set associated with this import process."
    )

    class Meta:
        verbose_name = 'Magento Import Attribute Set'
        verbose_name_plural = 'Magento Import Attribute Sets'

    def __str__(self):
        return f"Import process for {self.remote_attribute_set}"

class MagentoAttributeSetAttributeImport(ImportableModel):
    """
    Model representing the import process for attributes within a Magento Attribute Set.
    """

    remote_attribute = models.ForeignKey(
        'magento2.MagentoAttributeSetAttribute',
        on_delete=models.CASCADE,
        help_text="The remote attribute associated with this import process."
    )

    class Meta:
        verbose_name = 'Magento Import Attribute Set Attribute'
        verbose_name_plural = 'Magento Import Attribute Set Attributes'

    def __str__(self):
        return f"Import process for {self.remote_attribute}"
