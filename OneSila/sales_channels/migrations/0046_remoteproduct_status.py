from django.db import migrations, models


def populate_remote_product_status(apps, schema_editor):
    RemoteProduct = apps.get_model('sales_channels', 'RemoteProduct')
    IntegrationLog = apps.get_model('integrations', 'IntegrationLog')

    status_completed = 'COMPLETED'
    status_failed = 'FAILED'
    status_processing = 'PROCESSING'

    for remote_product in RemoteProduct.objects.all().iterator(chunk_size=500):
        if _has_unresolved_errors(IntegrationLog, remote_product.id):
            status = status_failed
        elif remote_product.syncing_current_percentage == 100:
            status = status_completed
        else:
            status = status_processing

        RemoteProduct.objects.filter(pk=remote_product.pk).update(status=status)


def _has_unresolved_errors(IntegrationLog, remote_product_id):
    failed_status = getattr(IntegrationLog, 'STATUS_FAILED', 'FAILED')
    success_status = getattr(IntegrationLog, 'STATUS_SUCCESS', 'SUCCESS')

    logs = list(
        IntegrationLog.objects.filter(remote_product_id=remote_product_id)
        .order_by('identifier', '-created_at')
    )

    latest_by_identifier = {}
    for log in logs:
        key = log.identifier if log.identifier is not None else '__none__'
        if key not in latest_by_identifier:
            latest_by_identifier[key] = log

    for log in latest_by_identifier.values():
        if log.status != failed_status:
            continue

        fixing_identifier = getattr(log, 'fixing_identifier', None)
        if fixing_identifier:
            fixed_exists = IntegrationLog.objects.filter(
                remote_product_id=remote_product_id,
                identifier=fixing_identifier,
                status=success_status,
                created_at__gt=log.created_at,
            ).exists()
            if fixed_exists:
                continue

        return True

    return False


class Migration(migrations.Migration):

    dependencies = [
        ('sales_channels', '0045_saleschannelcontenttemplate_add_as_iframe'),
        ('integrations', '0009_alter_integrationlog_related_object_str'),
    ]

    operations = [
        migrations.AddField(
            model_name='remoteproduct',
            name='status',
            field=models.CharField(
                choices=[('COMPLETED', 'Completed'), ('FAILED', 'Failed'), ('PROCESSING', 'Processing')],
                db_index=True,
                default='PROCESSING',
                help_text='Current sync status derived from progress and sync errors.',
                max_length=16,
            ),
            preserve_default=False,
        ),
        migrations.RunPython(populate_remote_product_status, migrations.RunPython.noop),
    ]
