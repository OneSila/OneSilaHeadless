# Generated by Django 4.2.5 on 2023-09-22 13:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('django_shared_multi_tenant', '0007_alter_multitenantcompany_language'),
    ]

    operations = [
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('unit', models.CharField(max_length=5)),
                ('multi_tenant_company', models.ForeignKey(blank=True, null=True,
                 on_delete=django.db.models.deletion.PROTECT, to='django_shared_multi_tenant.multitenantcompany')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]