# Generated by Django 5.0 on 2024-03-06 16:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0016_remove_linkedinpost_action_remove_linkedinpost_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="ID_content",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
