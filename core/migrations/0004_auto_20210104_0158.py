# Generated by Django 3.1.4 on 2021-01-03 22:58

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20210103_1421'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='cost',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='trip',
            name='datetime_paid',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='datetime rent start'),
            preserve_default=False,
        ),
    ]