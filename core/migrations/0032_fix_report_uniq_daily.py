from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0031_migrate_profile_images"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="report",
            name="uniq_daily_report",
        ),
        migrations.AddConstraint(
            model_name="report",
            constraint=models.UniqueConstraint(
                fields=["reporter", "reported", "reason", "created_date"],
                name="uniq_daily_report",
                condition=models.Q(status="PENDING"),
            ),
        ),
    ]
