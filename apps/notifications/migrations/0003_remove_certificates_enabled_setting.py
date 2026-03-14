from django.db import migrations


def remove_certificates_enabled_setting(apps, schema_editor):
    SystemSetting = apps.get_model("notifications", "SystemSetting")
    SystemSetting.objects.filter(setting_key="certificates_enabled").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0002_alter_notification_notification_type_and_more"),
    ]

    operations = [
        migrations.RunPython(
            remove_certificates_enabled_setting,
            migrations.RunPython.noop,
        ),
    ]
