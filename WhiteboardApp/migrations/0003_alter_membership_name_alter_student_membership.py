# Generated by Django 4.1.9 on 2023-07-09 21:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("WhiteboardApp", "0002_alter_membership_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="membership",
            name="name",
            field=models.CharField(
                choices=[
                    ("no", "No-Membership"),
                    ("gold", "Gold"),
                    ("silver", "Silver"),
                    ("bronze", "Bronze"),
                ],
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name="student",
            name="membership",
            field=models.ForeignKey(
                default="no",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="WhiteboardApp.membership",
            ),
        ),
    ]
