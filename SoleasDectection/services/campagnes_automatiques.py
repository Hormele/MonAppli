from django.utils import timezone
from django.apps import apps
from django.core.mail import send_mail
import pandas as pd
import pickle
import os

# Récupérer dynamiquement les modèles pour être sûr que Celery les trouve
Campagne = apps.get_model('SoleasDectection', 'Campagne')
Rapport = apps.get_model('SoleasDectection', 'Rapport')
Notification = apps.get_model('SoleasDectection', 'Notification')

def executer_automatiquement_les_campagnes():
    """
    Fonction principale qui vérifie les campagnes planifiées
    et lance celles qui doivent être exécutées.
    """
    now = timezone.now()

    # Récupérer les campagnes en attente ou suspendues
    campagnes = Campagne.objects.filter(statut__in=["en_attente", "suspendue"])

    for campagne in campagnes:

        # Vérifier que la campagne doit démarrer maintenant
        if campagne.date_debut_c <= now:
            print(f"➡ Lancement automatique de la campagne {campagne.id}")

            # Démarrer la campagne
            campagne.demarrer_campagne()

            # Pour chaque dataset lié
            datasets = campagne.datasets.all()
            for dataset in datasets:
                if not dataset.fichier:
                    continue  # Dataset vide → on saute

                # Lire le fichier CSV
                df = pd.read_csv(dataset.fichier.path)

                # Charger le modèle ML
                modele = campagne.modele_ml
                if not modele.fichier_modele:
                    continue  # Modèle absent → on saute

                with open(modele.fichier_modele.path, "rb") as f:
                    pipeline = pickle.load(f)

                # Nettoyage des données
                numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                df[numeric_cols] = df[numeric_cols].fillna(0)
                X = df[numeric_cols]

                # Faire les prédictions
                predictions = pipeline.predict(X)

                # Générer les rapports individuels en base
                for i, prediction in enumerate(predictions):
                    Rapport.objects.create(
                        nom=f"User Auto {i}",
                        matricule=f"{i}",
                        prediction=prediction,
                        description="Normal" if prediction == 1 else "Fraude détectée",
                        statut="en_attente",
                        campagne=campagne
                    )

                # Générer et enregistrer le rapport global CSV
                df['resultat_prediction'] = predictions
                dossier_campagne = f"media/rapports/campagne_{campagne.id}"
                if not os.path.exists(dossier_campagne):
                    os.makedirs(dossier_campagne)

                rapport_csv_path = f"{dossier_campagne}/rapport.csv"
                df.to_csv(rapport_csv_path, index=False)

                # Enregistrer le rapport global
                Rapport.objects.create(
                    campagne=campagne,
                    fichier=rapport_csv_path
                )

            # Notifier sur le Dashboard
            Notification.objects.create(
                titre="Campagne automatique terminée",
                message=f"La campagne {campagne} est terminée et un rapport a été généré.",
                utilisateur=None
            )

            # Notifier par email
            send_mail(
                subject=f"Campagne automatique terminée",
                message=f"La campagne {campagne.id} est terminée et le rapport a été généré avec succès.",
                from_email='noreply@monsite.com',
                recipient_list=['admin@example.com'],  # Change vers ton admin email
                fail_silently=True,
            )

            # Terminer la campagne
            campagne.arreter_campagne()