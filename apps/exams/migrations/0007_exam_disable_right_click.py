from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("exams", "0006_exam_require_camera_exam_require_microphone"),
    ]

    operations = [
        migrations.AddField(
            model_name="exam",
            name="disable_right_click",
            field=models.BooleanField(default=True),
        ),
    ]
