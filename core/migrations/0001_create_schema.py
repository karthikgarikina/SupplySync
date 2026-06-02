from django.db import migrations


def create_supplysync_schema(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("CREATE SCHEMA IF NOT EXISTS supplysync;")


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunPython(create_supplysync_schema, migrations.RunPython.noop),
    ]

