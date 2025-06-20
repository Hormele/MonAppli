# Generated by Django 5.2 on 2025-05-21 13:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("SoleasDectection", "0013_modeletest_fichier_suspects_temp"),
    ]

    operations = [
        migrations.CreateModel(
            name="FichierSuspectsTest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("fichier_csv", models.FileField(upload_to="suspects_test/")),
                ("date_enregistrement", models.DateTimeField(auto_now_add=True)),
                (
                    "modele_test",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="SoleasDectection.modeletest",
                    ),
                ),
            ],
        ),
    ]
