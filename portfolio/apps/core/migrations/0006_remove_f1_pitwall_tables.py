"""Drop leftover f1_pitwall database objects after app removal."""

from django.db import migrations

F1_TABLES = (
    'f1_pitwall_racecontrolmessage',
    'f1_pitwall_pitstop',
    'f1_pitwall_stint',
    'f1_pitwall_weatherdata',
    'f1_pitwall_lapdata',
    'f1_pitwall_telemetrysnapshot',
    'f1_pitwall_apiauditlog',
    'f1_pitwall_f1userprofile',
    'f1_pitwall_threatevent',
    'f1_pitwall_session',
    'f1_pitwall_driver',
)


def drop_f1_pitwall_schema(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        for table in F1_TABLES:
            cursor.execute(
                f'DROP TABLE IF EXISTS {connection.ops.quote_name(table)} CASCADE',
            )
        cursor.execute(
            """
            DELETE FROM auth_permission
            WHERE content_type_id IN (
                SELECT id FROM django_content_type WHERE app_label = %s
            )
            """,
            ['f1_pitwall'],
        )
        cursor.execute(
            """
            DELETE FROM django_admin_log
            WHERE content_type_id IN (
                SELECT id FROM django_content_type WHERE app_label = %s
            )
            """,
            ['f1_pitwall'],
        )
        cursor.execute(
            'DELETE FROM django_content_type WHERE app_label = %s',
            ['f1_pitwall'],
        )
        cursor.execute(
            'DELETE FROM django_migrations WHERE app = %s',
            ['f1_pitwall'],
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_project_view_url_optional'),
    ]

    operations = [
        migrations.RunPython(
            drop_f1_pitwall_schema,
            migrations.RunPython.noop,
        ),
    ]
