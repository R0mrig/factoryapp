# Generated by Django 5.0 on 2024-01-10 16:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0006_article_user_comment"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="content_size",
            field=models.CharField(default="", max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="article",
            name="goals",
            field=models.CharField(default="", max_length=200, null=True),
        ),
    ]
