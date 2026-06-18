from django.db import migrations, models


DEFAULT_TOPBAR_LINKS = (
    {
        'key': 'cv',
        'url': (
            'https://docs.google.com/document/d/11DNF9pFl0wQLNXac779DO6axLG67nMGIBC'
            '_bPTPulRQ/edit?usp=share_link'
        ),
        'title': 'CV',
        'icon_class': 'fas fa-user-cog',
        'ordering': 0,
    },
    {
        'key': 'github',
        'url': 'https://github.com/SerhiiKarnaukh',
        'title': 'GitHub Account',
        'icon_class': 'fab fa-github fw-normal',
        'ordering': 1,
    },
    {
        'key': 'linkedin',
        'url': 'https://www.linkedin.com/in/serhiikarnaukh',
        'title': 'LinkedIn Account',
        'icon_class': 'fab fa-linkedin-in fw-normal',
        'ordering': 2,
    },
)


def seed_topbar_links(apps, schema_editor):
    TopbarLink = apps.get_model('core', 'TopbarLink')
    for link in DEFAULT_TOPBAR_LINKS:
        TopbarLink.objects.create(**link)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_remove_f1_pitwall_tables'),
    ]

    operations = [
        migrations.CreateModel(
            name='TopbarLink',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                )),
                ('key', models.CharField(
                    choices=[
                        ('cv', 'CV'),
                        ('github', 'GitHub'),
                        ('linkedin', 'LinkedIn'),
                    ],
                    max_length=20,
                    unique=True,
                )),
                ('url', models.URLField(blank=True, default='')),
                ('title', models.CharField(max_length=100)),
                ('icon_class', models.CharField(max_length=100)),
                ('ordering', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Topbar link',
                'verbose_name_plural': 'Topbar links',
                'ordering': ['ordering', 'key'],
            },
        ),
        migrations.RunPython(seed_topbar_links, migrations.RunPython.noop),
    ]
