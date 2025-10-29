from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sales_channels", "0047_alter_remoteproduct_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="saleschannel",
            name="gpt_enable",
            field=models.BooleanField(
                default=False,
                help_text="Enable GPT-generated product feed configuration.",
            ),
        ),
        migrations.AddField(
            model_name="saleschannel",
            name="gpt_enable_checkout",
            field=models.BooleanField(
                default=False,
                help_text="Allow GPT-generated content to power checkout experiences.",
            ),
        ),
        migrations.AddField(
            model_name="saleschannel",
            name="gpt_seller_name",
            field=models.CharField(
                blank=True,
                help_text="Display name presented in GPT-powered experiences.",
                max_length=255,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="saleschannel",
            name="gpt_seller_url",
            field=models.URLField(
                blank=True,
                help_text="Uses the hostname by default; override here to present a different seller URL.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="saleschannel",
            name="gpt_seller_privacy_policy",
            field=models.URLField(
                blank=True,
                help_text="Link to your privacy policy when GPT checkout is enabled.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="saleschannel",
            name="gpt_seller_tos",
            field=models.URLField(
                blank=True,
                help_text="Link to your terms of service when GPT checkout is enabled.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="saleschannel",
            name="gpt_return_policy",
            field=models.URLField(
                blank=True,
                help_text="Public return policy URL required when GPT is enabled.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="saleschannel",
            name="gpt_return_window",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Return window (for example, in days) required when GPT is enabled.",
                null=True,
            ),
        ),
    ]
