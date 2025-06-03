from django.urls import path
from . import views
urlpatterns = [
    #route pour mon profil
    path('mon_profil/', views.mon_profil, name='mon_profil'),
    path('mon_profil/editer/', views.edit_profil, name='edit_profil'),

    #1 route pour le dashboard d'accueil
    path('dashboard_accueil/', views.dashboard_accueil, name='dashboard_accueil'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/analyste/', views.dashboard_analyste, name='dashboard_analyste'),
    
    #2. Route pour dashboard dataset
    path('datasets/', views.liste_datasets, name='liste_datasets'),
    path('datasets/uploader/', views.uploader_dataset, name='uploader_dataset'),
    path('datasets/supprimer/<int:dataset_id>/', views.supprimer_dataset, name='supprimer_dataset'),
 
    #3. #routes pour le dashboard modele_ml
    path('modeles/', views.liste_modeles, name='liste_modeles'),
    path('modeles/supprimer/<int:modele_id>/', views.supprimer_modele, name='supprimer_modele'),
    path('modeles/entrainer/', views.entrainer_modele_view, name='entrainer_modele'),

    # routes Campagne test
    path('campagne_test/lancer_campagne_test/', views.lancer_campagne_test_view, name='lancer_campagne_test'), #ok
    path('campagne_test/liste_campagne_test/', views.liste_campagne_test_view, name='liste_campagne_test'), #ok
    path('campagne_test/upload/', views.uploader_resultats_fraude, name='uploader_resultats_fraude'), #ok
    #path("gestionnaire/suspects/", views.liste_suspects_test_view, name="liste_suspects"),#ok
    path('gestionnaire/detail/<int:fichier_id>/', views.detail_campagne_test_view, name='detail_test'), #ok

    path('campagne_test/<int:fichier_id>/rapport/', views.generer_rapport_test_pdf, name='generer_rapport_test_pdf'),
    path('campagne_test/supprimer/<int:test_id>/', views.supprimer_campagne_test, name='supprimer_modele_test'),
    path('gestionnaire/test/<int:fichier_id>/supprimer/', views.supprimer_liste_test, name='supprimer_liste_test'),

    #4. Routes pour le dashboard campagne
    path('campagnes/lancer/', views.lancer_campagne, name='lancer_campagne'),
    path('campagnes/', views.liste_campagnes, name='liste_campagnes'),
    path('campagnes/demarrer/<int:id>/', views.demarrer_campagne, name='demarrer_campagne'),
    path('campagnes/suspendre/<int:id>/', views.suspendre_campagne, name='suspendre_campagne'),
    path('campagnes/arreter/<int:id>/', views.arreter_campagne, name='arreter_campagne'),
    path('campagnes/arreter/<int:id>/', views.reprendre_campagne, name='reprendre_campagne'),
    path('notifications/', views.liste_notifications, name='liste_notifications'),
    path('campagne/<int:campagne_id>/', views.detail_campagne, name='detail_campagne'),

    #Routes pour le dashboard gestionnaire risque
    path('dashboard_gestionnaire/', views.dashboard_gestionnaire, name='dashboard_gestionnaire'),
    path('suspect/<int:suspect_id>/bloquer/', views.bloquer_suspect, name='bloquer_suspect'),
    path('suspect/<int:suspect_id>/legitimer/', views.legitimer_suspect, name='legitimer_suspect'),
    path('suspect/<int:suspect_id>/attente/', views.attente_suspect, name='attente_suspect'),

    path('gestionnaire/campagnes/', views.gestionnaire_campagnes, name='gestionnaire_campagnes'),
    path('rapport/detail/<int:campagne_id>/', views.gestion_rapport_detail, name='gestion_rapport_detail'),
    path('gestionnaire/campagne/<int:campagne_id>/suspects/', views.gestionnaire_suspects, name='gestionnaire_suspects'),
    path('gestionnaire/suspect/<int:suspect_id>/decision/', views.prendre_decision_suspect, name='prendre_decision_suspect'),
    path('gestionnaire/regles/', views.gestionnaire_regles_metier, name='gestionnaire_regles_metier'),
    path('gestionnaire/regles/ajouter/', views.ajouter_regles_metier, name='ajouter_regle_metier'),
    path('gestionnaire/regles/modifier/<int:regle_id>/', views.modifier_regles_metier, name='modifier_regle_metier'),
    path('gestionnaire/regles/supprimer/<int:regle_id>/', views.supprimer_regles_metier, name='supprimer_regle_metier'),
    path('gestionnaire/regles/<int:regle_id>/toggle/', views.toggle_regle_metier, name='toggle_regle_metier'),
    path('gestionnaire/notifications/', views.gestionnaire_notifications, name='gestionnaire_notifications'),
    path('rapport/pdf/<int:campagne_id>/', views.exporter_rapport_pdf, name='exporter_rapport_pdf'),

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