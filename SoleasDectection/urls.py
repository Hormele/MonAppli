from django.urls import path
from . import views
urlpatterns = [
    #1 route pour le dashboard d'accueil
    path('dashboard_accueil/', views.dashboard_accueil, name='dashboard_accueil'),
    path('dashboard/admin', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/analyste', views.dashboard_analyste, name='dashboard_analyste'),
    #2. Route pour dashboard dataset
    path('datasets/', views.liste_datasets, name='liste_datasets'),
    path('datasets/uploader/', views.uploader_dataset, name='uploader_dataset'),
    path('datasets/supprimer/<int:dataset_id>/', views.supprimer_dataset, name='supprimer_dataset'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
 
    #3. #routes pour le dashboard modele_ml
    path('modeles/', views.liste_modeles, name='liste_modeles'),
    path('modeles/supprimer/<int:modele_id>/', views.supprimer_modele, name='supprimer_modele'),
    path('modeles/entrainer/', views.entrainer_modele_view, name='entrainer_modele'),
    path('modeles/tester/', views.tester_modele, name='tester_modele'),

    #4. Routes pour le dashboard campagne
    path('campagnes/lancer/', views.lancer_campagne, name='lancer_campagne'),
    path('campagnes/', views.liste_campagnes, name='liste_campagnes'),
    path('campagnes/demarrer/<int:id>/', views.demarrer_campagne, name='demarrer_campagne'),
    path('campagnes/suspendre/<int:id>/', views.suspendre_campagne, name='suspendre_campagne'),
    path('campagnes/arreter/<int:id>/', views.arreter_campagne, name='arreter_campagne'),
    path('notifications/', views.liste_notifications, name='utilisteur_notifications'),
    path('campagne/<int:campagne_id>/', views.detail_campagne, name='detail_campagne'),

    #Routes pour le dashboard gestionnaire risque
    path('dashboard/gestionnaire/', views.dashboard_gestionnaire, name='dashboard_gestionnaire'),
    path('dashboard_gestionnaire/', views.dashboard_gestionnaire, name='dashboard_gestionnaire'),
    path('gestionnaire/campagnes/', views.gestionnaire_campagnes, name='gestionnaire_campagnes'),
    path('gestionnaire/rapport/<int:campagne_id>/', views.consulter_rapport_campagne, name='consulter_rapport'),
    path('gestionnaire/campagne/<int:campagne_id>/suspects/', views.gestionnaire_suspects, name='gestionnaire_suspects'),
    path('gestionnaire/suspect/<int:suspect_id>/decision/', views.prendre_decision_suspect, name='prendre_decision_suspect'),
    path('gestionnaire/regles/', views.gestionnaire_regles_metier, name='gestionnaire_regles_metier'),
    path('gestionnaire/regles/ajouter/', views.ajouter_regles_metier, name='ajouter_regle_metier'),
    path('gestionnaire/regles/modifier/<int:regle_id>/', views.modifier_regles_metier, name='modifier_regle_metier'),
    path('gestionnaire/regles/supprimer/<int:regle_id>/', views.supprimer_regles_metier, name='supprimer_regle_metier'),
    path('gestionnaire/regles/<int:regle_id>/toggle/', views.toggle_regle_metier, name='toggle_regle_metier'),
    path('gestionnaire/notifications/', views.gestionnaire_notifications, name='gestionnaire_notifications'),
    path('gestionnaire/rapport/<int:campagne_id>/export/pdf/', views.exporter_rapport_pdf, name='exporter_rapport_pdf'),

    # Routes pour dashboard utilisateur
    path('utilisateur/regles/ajouter/', views.ajouter_regles_metier, name='ajouter_regle_metier'),
    path('utilisateur/utilisateurs/', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('utilisateur/utilisateur/ajouter/', views.ajouter_utilisateur, name='ajouter_utilisateur'),
    path('utilisateur/utilisateur/modifier/<int:user_id>/', views.modifier_utilisateur, name='modifier_utilisateur'),
    path('utilisateur/utilisateur/supprimer/<int:user_id>/', views.supprimer_utilisateur, name='supprimer_utilisateur'),

    # Authentification
    path('login/', views.connexion_view, name='login'),
    path('logout/', views.deconnexion_view, name='logout'),
]