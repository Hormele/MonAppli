# pour enregister la tache de lancement automatiques des campagnes
from celery import shared_task
from .models import Campagne
from .services.campagnes_automatiques import executer_automatiquement_les_campagnes

@shared_task
def lancer_campagnes_automatiques():
    campagnes = Campagne.objects.filter(statut='en_attente', automatique=True)
    