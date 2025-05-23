# Generated by Django 5.2 on 2025-04-10 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_multitenantcompany_language_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='multitenantcompany',
            name='languages',
            field=models.JSONField(blank=True, default=list, help_text='List of enabled language codes for this company.'),
        ),
        migrations.AlterField(
            model_name='multitenantcompany',
            name='language',
            field=models.CharField(choices=[('en', 'English'), ('fr', 'French'), ('nl', 'Dutch'), ('de', 'German'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pl', 'Polish'), ('ro', 'Romanian'), ('bg', 'Bulgarian'), ('hr', 'Croatian'), ('cs', 'Czech'), ('da', 'Danish'), ('et', 'Estonian'), ('fi', 'Finnish'), ('el', 'Greek'), ('hu', 'Hungarian'), ('lv', 'Latvian'), ('lt', 'Lithuanian'), ('mt', 'Maltese'), (
                'sk', 'Slovak'), ('sl', 'Slovenian'), ('sv', 'Swedish'), ('th', 'Thai'), ('ja', 'Japanese'), ('zh-hans', 'Chinese (Simplified)'), ('hi', 'Hindi'), ('pt-br', 'Portuguese (Brazil)'), ('ru', 'Russian'), ('af', 'Afrikaans'), ('ar', 'Arabic'), ('he', 'Hebrew'), ('tr', 'Turkish'), ('id', 'Indonesian'), ('ko', 'Korean'), ('ms', 'Malay'), ('vi', 'Vietnamese'), ('fa', 'Persian'), ('ur', 'Urdu')], default='en', max_length=7),
        ),
        migrations.AlterField(
            model_name='multitenantuser',
            name='language',
            field=models.CharField(choices=[('en', 'English'), ('fr', 'French'), ('nl', 'Dutch'), ('de', 'German'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pl', 'Polish'), ('ro', 'Romanian'), ('bg', 'Bulgarian'), ('hr', 'Croatian'), ('cs', 'Czech'), ('da', 'Danish'), ('et', 'Estonian'), ('fi', 'Finnish'), ('el', 'Greek'), ('hu', 'Hungarian'), ('lv', 'Latvian'), ('lt', 'Lithuanian'), ('mt', 'Maltese'), (
                'sk', 'Slovak'), ('sl', 'Slovenian'), ('sv', 'Swedish'), ('th', 'Thai'), ('ja', 'Japanese'), ('zh-hans', 'Chinese (Simplified)'), ('hi', 'Hindi'), ('pt-br', 'Portuguese (Brazil)'), ('ru', 'Russian'), ('af', 'Afrikaans'), ('ar', 'Arabic'), ('he', 'Hebrew'), ('tr', 'Turkish'), ('id', 'Indonesian'), ('ko', 'Korean'), ('ms', 'Malay'), ('vi', 'Vietnamese'), ('fa', 'Persian'), ('ur', 'Urdu')], default='en', max_length=7),
        ),
    ]
