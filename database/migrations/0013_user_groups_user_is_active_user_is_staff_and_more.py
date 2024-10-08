# Generated by Django 5.0 on 2024-01-30 16:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("database", "0012_article_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="groups",
            field=models.ManyToManyField(
                blank=True,
                help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                related_name="user_set",
                related_query_name="user",
                to="auth.group",
                verbose_name="groups",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="active"),
        ),
        migrations.AddField(
            model_name="user",
            name="is_staff",
            field=models.BooleanField(default=False, verbose_name="staff status"),
        ),
        migrations.AddField(
            model_name="user",
            name="is_superuser",
            field=models.BooleanField(
                default=False,
                help_text="Designates that this user has all permissions without explicitly assigning them.",
                verbose_name="superuser status",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="last_login",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="last login"
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="password",
            field=models.CharField(
                default="my_default_password", max_length=128, verbose_name="password"
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="user_permissions",
            field=models.ManyToManyField(
                blank=True,
                help_text="Specific permissions for this user.",
                related_name="user_set",
                related_query_name="user",
                to="auth.permission",
                verbose_name="user permissions",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="company_name",
            field=models.CharField(
                max_length=100, null=True, verbose_name="company name"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="company_url",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="company url"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                max_length=254, unique=True, verbose_name="email address"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="first_name",
            field=models.CharField(
                max_length=100, null=True, verbose_name="first name"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="last_name",
            field=models.CharField(max_length=100, null=True, verbose_name="last name"),
        ),
        migrations.AlterField(
            model_name="user",
            name="linkedin_url",
            field=models.URLField(blank=True, null=True, verbose_name="linkedin url"),
        ),
        migrations.AlterField(
            model_name="user",
            name="title",
            field=models.CharField(max_length=100, null=True, verbose_name="title"),
        ),
        migrations.AlterField(
            model_name="user",
            name="youtube_url",
            field=models.URLField(blank=True, null=True, verbose_name="youtube url"),
        ),
    ]
