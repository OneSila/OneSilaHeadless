from datetime import timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def cleanup_import_logs_flow():
    from sales_channels.models import (
        ImportProperty,
        ImportPropertySelectValue,
        ImportProduct,
    )
    from sales_channels.integrations.magento2.models import MagentoAttributeSetImport

    cutoff_date = timezone.now() - timedelta(days=90)
    models = [
        ImportProperty,
        ImportPropertySelectValue,
        ImportProduct,
        MagentoAttributeSetImport,
    ]

    total_deleted = 0

    for model in models:
        deleted_count, _ = model.objects.filter(created_at__lt=cutoff_date).delete()
        total_deleted += deleted_count

    logger.info(f"[CLEANUP] Deleted {total_deleted} old import entries.")