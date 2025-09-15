from django.db import migrations


def delete_browse_nodes(apps, schema_editor):
    AmazonBrowseNode = apps.get_model('amazon', 'AmazonBrowseNode')
    AmazonBrowseNode.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('amazon', '0057_amazonbrowsenode_parent_node'),
    ]

    operations = [
        migrations.RunPython(delete_browse_nodes, migrations.RunPython.noop),
    ]
