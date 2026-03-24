from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_planoption'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcessedWebhookEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_id', models.CharField(db_index=True, max_length=255, unique=True)),
                ('event_type', models.CharField(max_length=100)),
                ('processed_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['event_id'], name='payments_pro_event_i_idx'),
                ],
            },
        ),
    ]
