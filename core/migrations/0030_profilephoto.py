import core.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0029_userprofile_deleted_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfilePhoto',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=core.models._profile_photo_path)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile_photos',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['order', 'created_at'],
                'indexes': [
                    models.Index(fields=['user', 'order'], name='core_profilephoto_user_order_idx'),
                ],
            },
        ),
    ]
