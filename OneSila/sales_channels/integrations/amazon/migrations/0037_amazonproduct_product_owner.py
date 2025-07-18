from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0036_alter_amazonproducttype_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='amazonproduct',
            name='product_owner',
            field=models.BooleanField(default=False, help_text='Indicates if this listing was created by us and we can manage listing level data.'),
        ),
    ]
