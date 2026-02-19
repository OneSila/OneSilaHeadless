from django.db import migrations
from django.db.models import OuterRef, Subquery


def forwards(apps, schema_editor):
    RemoteProperty = apps.get_model("sales_channels", "RemoteProperty")
    RemotePropertySelectValue = apps.get_model("sales_channels", "RemotePropertySelectValue")

    allow_multiple_subquery = RemoteProperty.objects.filter(
        pk=OuterRef("remote_property_id")
    ).values("allow_multiple")[:1]
    RemotePropertySelectValue.objects.update(
        allow_multiple=Subquery(allow_multiple_subquery)
    )


def backwards(apps, schema_editor):
    RemotePropertySelectValue = apps.get_model("sales_channels", "RemotePropertySelectValue")
    RemotePropertySelectValue.objects.update(allow_multiple=False)


class Migration(migrations.Migration):

    dependencies = [
        ("sales_channels", "0072_alter_remotepropertyselectvalue_unique_together_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
