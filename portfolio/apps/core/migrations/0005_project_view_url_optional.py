# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_serverstatistics'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='view_url',
            field=models.URLField(blank=True, max_length=200),
        ),
    ]
