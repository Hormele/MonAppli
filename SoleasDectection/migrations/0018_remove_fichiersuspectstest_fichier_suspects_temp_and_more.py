# Generated by Django 5.2 on 2025-05-22 00:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("SoleasDectection", "0017_remove_modeletest_fichier_suspects_temp_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="fichiersuspectstest",
            name="fichier_suspects_temp",
        ),
        migrations.AddField(
            model_name="modeletest",
            name="fichier_suspects_temp",
            field=models.FileField(blank=True, null=True, upload_to="suspects_temp/"),
        ),
    ]
