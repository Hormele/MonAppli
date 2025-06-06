import pickle
import os, json
import pandas as pd
from xhtml2pdf import pisa
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.db.models import Count
from django.contrib import messages
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.db.models.functions import ExtractMonth
from django.template.loader import get_template
from django.shortcuts import render, redirect, get_object_or_404
from .services.train_model import entrainer_modele, tester_campagne_test
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import LoginForm, ProfilForm, UtilisateurCreationForm
from .models import Campagne, Utilisateur, Dataset, GestionnaireRisque, Notification, ModeleML, RegleMetier, CampagneTest, SuspectTest, FichierSuspectsTest



def admin_required(view_func):
    decorated_view_func = user_passes_test(lambda u: u.is_authenticated and u.role == 'admin')(view_func)
    return decorated_view_func


Utilisateur = get_user_model()



#1.-------------------- VUE POUR LE DASHBOARD D'ACCEUIL----------------------
def dashboard_accueil(request):
    return render(request, 'dashboard_accueil.html')

#-------------------------- VUE DASHBOARD ADMIN 
def dashboard_admin(request):
    # Cartes de résumé
    users_count = Utilisateur.objects.count()
    campaigns_count = CampagneTest.objects.filter(statut='en cours').count()
    finished_campaigns_count = CampagneTest.objects.filter(statut='terminee').count()
    datasets_count = Dataset.objects.count()

    # Données pour le graphique des datasets par mois
    datasets_par_mois = Dataset.objects.annotate(
        month=ExtractMonth('dateC')
    ).values('month').annotate(
        total=Count('id')
    ).order_by('month')

    print ("datasets_par_mois :", list(datasets_par_mois))

    datasets_data = [0] * 12
    for d in datasets_par_mois:
        if d['month']:
            datasets_data[d['month'] - 1] = d['total']

    # Données pour le graphique des campagnes par mois
    campaigns_par_mois = CampagneTest.objects.annotate(
        month=ExtractMonth('date_test')  # change selon ton modèle
    ).values('month').annotate(
        total=Count('id')
    ).order_by('month')

    campaigns_data = [0] * 12
    for d in campaigns_par_mois:
        campaigns_data[d['month'] - 1] = d['total']

    # Labels des mois
    mois_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Préparer les données pour le template
    context = {
        'users_count': users_count,
        'campaigns_count': campaigns_count,
        'finished_campaigns_count': finished_campaigns_count,
        'datasets_count': datasets_count,
        'mois_labels': mois_labels,
        'datasets_data': datasets_data,
        'campaigns_data': campaigns_data,
    }

    return render(request, 'dashboard_admin.html', context)


#-------------------------------- VUE DASHBOARD ANALYSTE -----------------------
def dashboard_analyste(request):
    # Récupérer les données des campagnes
    campaigns_count = CampagneTest.objects.filter(statut='en cours').count()
    finished_campaigns_count = CampagneTest.objects.filter(statut='terminee').count()
    datasets_count = Dataset.objects.count()

    # Récupérer les suspects
    suspects_legitime = SuspectTest.objects.filter(decision='légitime').count()
    suspects_bloque = SuspectTest.objects.filter(decision='bloque').count()
    suspects_attente = SuspectTest.objects.filter(decision='en attente').count()

    # Données pour le graphique des datasets par mois
    datasets_par_mois = Dataset.objects.annotate(
        month=ExtractMonth('dateC')
    ).values('month').annotate(
        total=Count('id')
    ).order_by('month')

    datasets_data = [0] * 12
    for d in datasets_par_mois:
        datasets_data[d['month'] - 1] = d['total']

    # Données pour le graphique des campagnes par mois
    campaigns_par_mois = CampagneTest.objects.annotate(
        month=ExtractMonth('date_test')  # change selon ton modèle
    ).values('month').annotate(
        total=Count('id')
    ).order_by('month')

    campaigns_data = [0] * 12
    for d in campaigns_par_mois:
        campaigns_data[d['month'] - 1] = d['total']

    # Labels des mois
    mois_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


    # Passer les données au contexte
    context = {
        'campaigns_count': campaigns_count,
        'finished_campaigns_count': finished_campaigns_count,
        'datasets_count': datasets_count,
        'suspects_legitime': suspects_legitime,
        'suspects_bloque': suspects_bloque,
        'suspects_attente': suspects_attente,
        'mois_labels': mois_labels,
        'datasets_data': datasets_data,
        'campaign_data': campaigns_data,
    }

    return render(request, 'dashboard_analyste.html', context)

#------------------------VUE MON PROFIL------------------
@login_required
def mon_profil(request):
    # Récupère les informations de l'utilisateur connecté
    user = request.user
    return render(request, 'mon_profil.html', {'user': user})


# ------------------------ vue pour modifier le profil -----------------------------------------------
@login_required
def edit_profil(request):
    if request.method == 'POST':
        form = ProfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('mon_profil')  # Redirige vers la page de profil après la modification
    else:
        form = ProfilForm(instance=request.user)
    return render(request, 'edit_profil.html', {'form': form})


#2. ----------------------- VUE DASHBOARD DATASET ----------------------------------------------------------------------------
#2-1. VUE POUR Liste des datasets + Statistiques -------------
def liste_datasets(request):
    # Récupérer tous les datasets
    datasets = Dataset.objects.all()

    # Gestion des filtres GET
    type_filtre = request.GET.get('type')
    format_filtre = request.GET.get('format_fichier')
    date_min = request.GET.get('date_min')
    date_max = request.GET.get('date_max')

    if type_filtre:
        datasets = datasets.filter(type=type_filtre)
    if format_filtre:
        datasets = datasets.filter(format_fichier=format_filtre)
    if date_min:
        datasets = datasets.filter(dateC__gte=date_min)
    if date_max:
        datasets = datasets.filter(dateC__lte=date_max)

    # Statistiques
    brut_count = datasets.filter(type='brut').count()
    nettoye_count = datasets.filter(type='nettoye').count()

    context = {
        'datasets': datasets,
        'brut_count': brut_count,
        'nettoye_count': nettoye_count,
    }
    return render(request, 'dataset/liste_datasets.html', context)

#2-2. VUE POUR Uploader un dataset--------------------------------------------------------

@login_required
def uploader_dataset(request):
    print(">>> Début de la vue uploader_dataset")
    message = None
    erreur = None

    if request.method == 'POST':
        print(">>> Formulaire POST reçu")

        nom_initial = request.POST.get('nom')
        type_fichier = request.POST.get('type')
        description = request.POST.get('description', '')

        fichier = request.FILES.get('fichier')
        fichier_brut = request.FILES.get('fichier_brut')

        if not fichier and not fichier_brut:
            message = "Veuillez sélectionner au moins un fichier à uploader."
            return render(request, 'modele/uploader_dataset.html', {
                'message': message,
                'erreur': erreur,
            })
        
        fichier_utilise = fichier if fichier else fichier_brut
        extension = os.path.splitext(fichier_utilise.name)[1].lower().replace('.', '')
        print(f">>> Extension détectée : {extension}")

        if extension not in ['csv', 'json']: # RETIRER JSON ICI ------------------------------------------------
            erreur = "Format de fichier non pris en charge (CSV ou JSON uniquement)."
            print(">>> Erreur : extension non supportée")
            return render(request, 'dataset/uploader_dataset.html', {'erreur': erreur})
        
        if type_fichier == 'nettoye':
            nom = f"{nom_initial.strip()}_cleaned"
        else:
            nom = nom_initial.strip()

        try:
            #extension_with_dot = os.path.splitext(fichier_utilise.name)[1].lower()
            #nom_base = nom_initial.lower().replace(' ', '_')

            #if nom_base.endswitch('_cleaned'):
                #nom_base = nom_base[:-8]

            #if type_fichier.lower() == 'nettoye' and fichier:
                #nom = f"{nom_base}_cleaned{extension_with_dot}"
            #elif fichier:
                #nom = f"{nom_base}{extension_with_dot}"
            #else:
                #nom = nom_base # si brut uniquement

            #fichier.name = nom
            print(f">>> Nom du fichier renommé : {fichier.name if fichier else 'aucun fichier renomme'}")
        
            dataset = Dataset.objects.create(
                nom=nom,
                description=description,
                type=type_fichier,
                format_fichier=extension,
                fichier=fichier if fichier else None,
                fichier_brut=fichier_brut if fichier_brut else None
            )
            print(f">>> Dataset enregistré avec ID {dataset.id}")

            message = "Le dataset a été uploadé avec succès."
            return redirect('liste_datasets')

        except Exception as e:
            erreur = f"Erreur lors de l'enregistrement : {str(e)}"
            print(f">>> Exception : {erreur}")

    print(">>> Fin de la vue uploader_dataset")
    return render(request, 'dataset/uploader_dataset.html', {
        'message': message,
        'erreur': erreur
    })

            
        
#2-3. VUE POUR Supprimer un dataset ----------------------------------------------------------------
@login_required
def supprimer_dataset(request, dataset_id):
    print("suppression en cours")
    dataset = get_object_or_404(Dataset, id=dataset_id)

    # Supprimer le fichier physique si présent
    if dataset.fichier and dataset.fichier.path:
        try:
            file_path = dataset.fichier.path
            if os.path.exists(file_path):
                os.remove(file_path)
                print(">>> Fichier supprimé :", file_path)
            else:
                print(">>> Fichier introuvable :", file_path)
        except Exception as e:
            print(">>> Erreur suppression fichier :", str(e))

    # Supprimer le fichier brut si présent
    if dataset.fichier_brut and dataset.fichier_brut.path:
        try:
            file_path_brut = dataset.fichier_brut.path
            if os.path.exists(file_path_brut):
                os.remove(file_path_brut)
                print(">>> Fichier supprimé :", file_path_brut)
            else:
                print(">>> Fichier introuvable :", file_path_brut)
        except Exception as e:
            print(">>> Erreur suppression fichier :", str(e))

    # Supprimer l’objet en base
    dataset.delete()
    print(">>> Dataset supprimé de la base")
    return redirect("liste_datasets")


#3.----------------------------------------- VUE POUR  Dashboard ModelML-----------------------------------------------------------------
#1. VUE POUR LISTER LES MODELES + Statistiques -----------
@login_required
def liste_modeles(request):
    # Récupérer les modèles de la base de données
    modeles = ModeleML.objects.all()

    # Filtrer par algorithme si un filtre est appliqué
    algo_filter = request.GET.get("algo")
    if algo_filter:
        modeles = modeles.filter(algorithme=algo_filter)

    # Filtrer par date si un filtre de date est appliqué
    date_filter = request.GET.get("date")
    if date_filter:
        modeles = modeles.filter(date_creation__date=date_filter)

    # Données pour les graphiques (statistiques par algorithme)
    algo_stats = (
        modeles.values("algorithme")
        .annotate(nombre=Count("id"))
        .order_by("algorithme")
    )
    algo_labels = [item["algorithme"] for item in algo_stats]
    algo_data = [item["nombre"] for item in algo_stats]

    # Données pour les graphiques (statistiques par type de fraude)
    fraude_stats = (
        modeles.values("type_fraude")
        .annotate(nombre=Count("id"))
        .order_by("type_fraude")
    )
    fraude_labels = [item["type_fraude"] for item in fraude_stats]
    fraude_data = [item["nombre"] for item in fraude_stats]

    # Passer les données au template
    context = {
        "modeles": modeles,
        "algo_labels": algo_labels,
        "algo_data": algo_data,
        "fraude_labels": fraude_labels,
        "fraude_data": fraude_data,
    }

    return render(request, "modele/liste_modeles.html", context)


# SUPPRIMER UN MODELE
@login_required
def supprimer_modele(request, modele_id):
    modele = ModeleML.objects.get(id=modele_id)

    # Supprimer fichier
    if modele.fichier_modele and os.path.exists(modele.fichier_modele.path):
        os.remove(modele.fichier_modele.path)

    modele.delete()
    return redirect('liste_modeles')

#2. VUE POUR ENTRAINER UN MODELE-----
@login_required
def entrainer_modele_view(request):
    print (">>> STUPID")
    datasets = Dataset.objects.filter(type='nettoye')  # Filtre les datasets nettoyés
    message = None
    erreur= None

    if request.method == "POST":
        print(">>> formulaire post recu")
        # Récupérer les données du formulaire
        dataset_id = request.POST.get("dataset")
        algorithme = request.POST.get("algorithme")
        type_fraude = request.POST.get("type_fraude")

        print(">>> donnees OK : dataset={dataset_id}, algo={algorithme}, type_fraude={type_fraude}")

        # Récupérer le dataset
        try:
            dataset = Dataset.objects.get(id=dataset_id)
            print(f" dataset trouve : {dataset.nom}")
        except Dataset.DoesNotExist:
            erreur = "Dataset non trouve"
            print(">>> datasetintrouvable")
            return render(request, 'modele/entrainer_modele.html', {
                'error': erreur, 
                'datasets': datasets
            })

        # Appeler la fonction d'entraînement
        try:
            # chemin absolue vers le fichier datatset
            dataset_path = dataset.fichier.path
            print(">>> url dataset :", dataset_path)
            if not os.path.exists(dataset_path):
                raise FileNotFoundError(f"Fichier dataset introuvablke : {dataset_path}")

            #chemin ou sauvegarder le modele entrainer
            modele_filename = f"{algorithme}_{dataset.nom}.pkl"
            modele_pkl_path = os.path.join(settings.MEDIA_ROOT, 'modeles_ml', modele_filename)
            print(">>> modele sauvegarder :", modele_pkl_path)

            # Entrainement du modele
            model_path = entrainer_modele(dataset_path, algorithme, modele_pkl_path)
            print(">>> modele entraine ok :", model_path)

            # Sauvegarder le modèle dans la base de données
            ModeleML.objects.create(
                nom=f"Modèle {dataset.nom} - {algorithme}",
                description=f"Modèle entraîné sur {dataset.nom}",
                algorithme=algorithme,
                type_fraude=type_fraude,
                fichier_modele=model_path
            )
            print(">>> enregistrement OK :")

            message = "Modele entrainee et sauvegarder avec success"


        except Exception as e:
            erreur = f"Erreur lors de l'entrainement du modele : {str(e)}"
            print(">>> erreur :", erreur)
            return render(request, 'modele/entrainer_modele.html', {'datasets': datasets})
            

        # Rediriger vers la liste des modèles après l'entraînement
        return redirect('liste_modeles')

    return render(request, 'modele/entrainer_modele.html', {
        'datasets': datasets,
        'message': message,
        'erreur': erreur
    })


#3.VUE POUR LANCER UNE CAPAGNE SUR UN DATASET NETTOYE ---
@login_required
def lancer_campagne_test_view(request):
    print(">>> Accès à la vue : tester_modele_view()")
    modeles = ModeleML.objects.all()
    datasets = Dataset.objects.filter(type='nettoye')

    if request.method == 'POST':
        print(">>> Formulaire POST reçu")
        modele_id = request.POST.get("modele")
        dataset_id = request.POST.get("dataset")

        try:
            modele = ModeleML.objects.get(id=modele_id)
            dataset = Dataset.objects.get(id=dataset_id)
            print(f">>> Modèle sélectionné : {modele.nom}")
            print(f">>> Dataset sélectionné : {dataset.nom}")

            if dataset.type != 'nettoye':
                raise ValueError("Le dataset sélectionné n'est pas de type 'nettoye'.")

            model_path = modele.fichier_modele.path
            dataset_path = dataset.fichier.path

            print(">>> Chemin modèle :", model_path)
            print(">>> Chemin dataset :", dataset_path)

            # Appliquer le modèle
            df_resultat, graph_data = tester_campagne_test(model_path, dataset_path)
            print(">>> Prédictions terminées")

            nb_fraudes = int(df_resultat['is_fraud'].sum())
            total = len(df_resultat)

            print("nb_fraudes a enregistrer:", nb_fraudes)
            print("total a enregistrer:", total)

            #recuperer les informations du modele
            #type_fraude = modele.type_fraude
            #algorithme = modele.algorithme

            # Sauvegarde du résultat
            result_filename = f"resultat_{modele.nom}_fraude.csv".replace(" ", "_")
            relative_result_path = os.path.join('resultats_fraude', result_filename)

            # Création du répertoire si nécessaire
            #result_path = os.path.join(settings.MEDIA_ROOT, relative_result_path)
            #os.makedirs(os.path.dirname(result_path), exist_ok=True)

            # Sauvegarde du DataFrame en CSV dans le répertoire approprié
            csv_bytes = df_resultat.to_csv(index=False).encode('utf-8')


            # Création du test dans la base de données
            campagne = CampagneTest.objects.create(
                modele=modele,
                dataset=dataset,
                statut='succes',  # Statut par défaut, peut être mis à jour selon le contexte
                nb_fraudes=nb_fraudes,
                nb_total=total,
                nom_fichier_resultat=result_filename,
                fichier_fraude=ContentFile(csv_bytes, name=result_filename),  # Chemin relatif pour le fichier
                graph_data=json.dumps(graph_data)  # Assurez-vous que `graph_data` est bien préparé
            )

            #with open (result_path, 'rb') as f:
                #campagne.fichier_fraude.save(result_filename, File(f), save=True)
            print(">>> campagne test sauvegardé dans la base")

            messages.success(request, f"{nb_fraudes} fraudes détectées sur {total} lignes. Rapport généré avec succès.")
            return redirect('liste_campagne_test')


        except Exception as e:
            print(">>> Erreur lors du test :", str(e))
            return render(request, "campagne_test/lancer_campagne_test.html", {
                "error": str(e),
                "modeles": modeles,
                "datasets": datasets
            })

    return render(request, "campagne_test/lancer_campagne_test.html", {
        "modeles": modeles,
        "datasets": datasets
    })


# VUE LISTE_CAMPAGNE_TEST -----------------------------------------
@login_required
def liste_campagne_test_view(request):
    # Récupérer les tests
    tests = CampagneTest.objects.all()
    print(f">>> Tous les tests avant filtrage : {tests.count()} tests")

    for test in tests:
        print(f"Test ID: {test.id}")  # Vérifier l'ID
    context = {
        'tests': tests,
    }

    # Gestion des filtres
    statut_filtre = request.GET.get('statut')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    # Filtrage par statut
    if statut_filtre:
        tests = tests.filter(statut=statut_filtre)

    # Filtrage par date (date_min et date_max)
    if date_debut:
        tests = tests.filter(date_test__gte=date_debut)
    if date_fin:
        tests = tests.filter(date_test__lte=date_fin)

    print(f">>> Tests après filtrage : {tests.count()} tests")

    # --- Statistiques pour le graphique des statuts ---
    success_count = tests.filter(statut='succes').count()
    failure_count = tests.filter(statut='echec').count()

    statut_labels = ['Success', 'Failure']
    statut_data = [success_count, failure_count]

    print(f">>> Statut des tests : {statut_data}")

    # Exemple : afficher les stats de prédiction du dernier test
    dernier_test = tests.last()

    if dernier_test and dernier_test.graph_data:
        try:
            graph_data = json.loads(dernier_test.graph_data)  # Convertir la chaîne en dictionnaire
        except json.JSONDecodeError:
            graph_data = {'labels': ['Normal (1)', 'Anomalie (-1)'], 'data': [0, 0]}
    else:
        graph_data = {'labels': ['Normal (1)', 'Anomalie (-1)'], 'data': [0, 0]}


    context = {
        'statut_labels': statut_labels,
        'statut_data': statut_data,
        'graph_labels': graph_data['labels'],
        'graph_values': graph_data['data'],
        'tests': tests,

    }

    return render(request, 'campagne_test/liste_campagne_test.html', context)


# Vue pour upload un fichier avec fraude et ressortir le detail des suspects
@login_required
def uploader_resultats_fraude(request):
    print(">>> STUPID")
    message = None
    erreur = None
    test = None

    # Récupérer les fichiers disponibles
    dossiers_resultats = os.path.join(settings.MEDIA_ROOT, 'resultats_fraude')
    dossiers_users = os.path.join(settings.MEDIA_ROOT, 'dataset_brut')
    dossiers_datasets = os.path.join(settings.MEDIA_ROOT, 'datasets')

    fichiers_resultats = [f for f in os.listdir(dossiers_resultats) if f.endswith('.csv')]
    fichiers_users = [f for f in os.listdir(dossiers_users) if f == 'user.csv']
    fichiers_datasets = [f for f in os.listdir(dossiers_datasets) if f.endswith('.csv')]
    regles = RegleMetier.objects.filter(actif=True)

    if request.method == 'POST':
        nom_resultat = request.POST.get('fichier_resultat')
        nom_user = request.POST.get('fichier_user')
        nom_dataset = request.POST.get('fichier_dataset')
        regles_selectionnees = request.POST.getlist('regles')
        test_id = request.GET.get('test_id') or request.POST.get('test_id')

        print(">>> Fichier résultat sélectionné :", nom_resultat)
        print(">>> Fichier user sélectionné :", nom_user)
        print(">>> Fichier dataset nettoye sélectionné :", nom_dataset)
        print(">>> Règles sélectionnées :", regles_selectionnees)
        print(">>> test ID reçu :", test_id)

        # Vérifications initiales
        if not nom_resultat or not nom_dataset or not nom_user:
            erreur = "Veuillez sélectionner les trois fichiers."
        elif not test_id:
            erreur = "ID du test manquant. Veuillez sélectionner un test valide."
        else:
            try:
                # Récupération du test associé
                test = CampagneTest.objects.filter(id=test_id).first() if test_id else None
                if not test:
                    erreur = "Aucun test avec cet ID n’a été trouvé."
                    raise ValueError(erreur)

                print(f">>> Test trouvé : {test}")

                chemin_resultat = os.path.join(dossiers_resultats, nom_resultat)
                chemin_user = os.path.join(dossiers_users, nom_user)
                chemin_dataset = os.path.join(dossiers_datasets, nom_dataset)

                print(">>> Chemin absolu du résultat :", chemin_resultat)
                print(">>> Chemin absolu du user_df :", chemin_user)
                print(">>> Chemin absolu du dataset :", chemin_dataset)

                # Chargement des données -----------------------------------
                # Chargement sécurisé des fichiers CSV
                try:
                    df_fraude = pd.read_csv(chemin_resultat)
                    df = pd.read_csv(chemin_dataset)  # df original (utile si d'autres colonnes sont utilisées)
                    user_df = pd.read_csv(chemin_user)  # pour traiter les ID comme string initialement
                except Exception as e:
                    raise ValueError(f"Erreur de lecture des fichiers CSV : {e}")

                # Sélection colonnes pertinentes pour user_df
                print(">>> Colonnes de user_df avant sélection :", user_df.columns.tolist())
                user_df = user_df[['id', 'username', 'matricule']]
                # Renommage du id
                user_df.rename(columns={'id': 'user_id'}, inplace=True)
                print(">>> Colonnes de user_df après renommage :", user_df.columns.tolist())

                # 3. Conversion des types
                df_fraude['user_id'] = df_fraude['user_id'].astype(int)
                user_df['user_id'] = user_df['user_id'].astype(int)
                df_fraude['user_id'] = range(1, len(df_fraude) + 1) # fais ressortir les vraies utilisateurs

                # 4. Fusion user_df + df_fraude
                df_rapport = pd.merge(df_fraude, user_df, on='user_id', how='left')
                print(">>> Colonnes après fusion :", df_rapport.columns.tolist())

                # Application des règles métiers
                print(">>> Application dynamique des règles métiers avec eval()")
                colonnes_regles = []
                regles = RegleMetier.objects.filter(id__in=regles_selectionnees, actif=True)

                for regle in regles:
                    nom_colonne = regle.nom
                    condition = regle.condition
                    

                    print(f">>> Application de la règle : {nom_colonne}")
                    print(f"    Condition : {condition}")

                    try:
                        # Appliquer la règle dynamiquement via eval sur chaque ligne
                        df[nom_colonne] = df.apply(lambda row: int(eval(condition, {}, {"row": row})), axis=1)
                        df_rapport[nom_colonne] = df[nom_colonne]
                        colonnes_regles.append(nom_colonne)
                        print(f">>> Colonne {nom_colonne} ajoutée avec succès.")
                    except Exception as e:
                        print(f"!!! Erreur lors de l'application de la règle {nom_colonne} : {e}")

                # Generer la descriptions------------------------------------------------
                print(">>> Generation du rapport.")
                def generer_description(row):
                    raisons = []
                    for regle in colonnes_regles:
                        try:
                            if row.get(regle, False):
                                regle_obj = RegleMetier.objects.filter(nom=regle).first()
                                if regle_obj:
                                    raisons.append(regle_obj.description)
                        except Exception as e:
                            print(f">>> Erreur dans regle {regle} : {e}")
                    if not raisons:
                        raisons.append("Utilisateur considere comme suspect.")
                    return " | ".join(raisons)

                # Appliquer si is_fraud == 1
                df_rapport['description'] = df_rapport.apply(
                    lambda row: generer_description(row) if row.get('is_fraud') == 1 else "", axis=1
                )

                print(">>> Génération des descriptions terminée.")
                print(">>> Aperçu des descriptions générées :")
                print(df_rapport[['user_id', 'description']].head())

                # Détection des colonnes à afficher
                if 'username_y' in df_rapport.columns and 'matricule_y' in df_rapport.columns:
                    username = 'username_y'
                    matricule = 'matricule_y'
                else:
                    username_col = 'username'
                    matricule_col = 'matricule'

                print(f">>>> username_col : {username_col}")
                print(f">>>> matricume_col : {matricule_col}")

                # Construction du rapport final
                print(">>> rapport final")
                colonnes_affichage = ['user_id', username_col, matricule_col, 'is_fraud', 'description']
                rapport_final = df_rapport[df_rapport['is_fraud'] == 1][colonnes_affichage]
                rapport_final.dropna(subset=['user_id', username_col, matricule_col], inplace=True) # supp des lignes incompletes
                rapport_final['user_id'] = rapport_final['user_id'].astype(int) # conversion user_id en int

                print(">>> Colonnes d'affichage :", colonnes_affichage)
                print(">>> colonnes reelles :", df_rapport.columns.tolist())
                print(rapport_final.head())

                # Enregistrement des suspects
                # Créer le dossier s'il n'existe pas
                base_dir = os.path.join(settings.MEDIA_ROOT, 'suspects_temp')
                os.makedirs(base_dir, exist_ok=True)

                 # Récupérer le nom du fichier de résultat (sans extension ni dossier)
                nom_resultat = os.path.splitext(os.path.basename(test.fichier_fraude.name))[0]

                # Générer le nom du fichier final
                file_name = f"suspects_{nom_resultat}.csv"
                file_path = os.path.join(base_dir, file_name)

                # Sauvegarder le rapport
                rapport_final.to_csv(file_path, index=False, encoding='utf-8')
                print(f">>> Fichier csv genere : {file_path}")

                # #Enregistrement fichier CSV dans FichierSuspectsTest
                #test = CampagneTest.objects.get(id=test_id)
                #if not test:
                    #erreur = "Aucun test avec cet ID n’a été trouvé."
                    #raise ValueError(erreur)

                #gestionnaire = GestionnaireRisque.objects.filter(campagne_test=test).first()
                #if not gestionnaire:
                    #print(">>> Aucun gestionnaire trouvé, création...")
                    #gestionnaire = GestionnaireRisque.objects.create(campagne_test=test)
                #print(f">>> Gestionnaire OK : {gestionnaire.id}")

                print(f">>> Tentative récupération gestionnaire pour test id {test.id}")
                fichier_obj = FichierSuspectsTest.objects.create(
                    campagne_test=test,
                    nom_fichier=file_name
                )
                test.fichier_suspects_temp.name = f"suspects_temp/{file_name}"
                test.save()

                message = "Résultats traités avec succès."

                print(">>> Enregistrement suspect")
                for _, row in rapport_final.iterrows():
                    SuspectTest.objects.create(
                        user_id=int(row['user_id']),
                        username=row[username_col],
                        matricule=row[matricule_col],
                        is_fraud=int(row['is_fraud']),
                        description=row['description'],
                        decision='en_attente',
                        campagne_test=test
                    )
    
                    print(">>> Suspect enregistre avec succes.")
                return redirect('dashboard_gestionnaire')

            except Exception as e:
                print(">>> ERREUR :", e)
                erreur = f"Erreur pendant le traitement : {e}"

    return render(request, 'campagne_test/uploader_resultats_fraude.html', {
        'fichiers_resultats': fichiers_resultats,
        'fichiers_datasets': fichiers_datasets,
        'fichiers_users': fichiers_users,
        'regles': regles,
        'test': test,
        'message': message,
        'erreur': erreur
    })

    
#@login_required
#def liste_suspects_test_view(request):
    #print("STUPID")
    #fichiers_suspects = FichierSuspectsTest.objects.all().order_by('-date_enregistrement')
    # Expoer CSV des suspects
    
    #context = {
        #'fichiers_suspects': fichiers_suspects,
    #}
    #print(">>> Liste des fichiers suspects détectés :", fichiers_suspects)
    #return render(request, 'gestionnaire/dashboard_gestionnaire.html', context)




# VUE DETAIL CAMPAGNE TEST-------------------------------
@login_required
def detail_campagne_test_view(request, fichier_id):
    fichier = get_object_or_404(FichierSuspectsTest, id=fichier_id)
    #test = fichier.modele_test  # Accès au ModeleTest lié

    # Construire le chemin complet vers le fichier CSV
    #chemin_csv = os.path.join(settings.MEDIA_ROOT, 'suspects_temp', fichier.campagne_test.fichier_suspects_temp.name)
    chemin_csv = os.path.join(settings.MEDIA_ROOT, 'suspects_temp', fichier.nom_fichier)


    if not os.path.exists(chemin_csv):
        erreur = "Le fichier de suspects est introuvable."
        return render(request, 'gestionnaire/detail_test.html', {
            'erreur': erreur,
            #'test': test,
            'fichier': fichier,
        })
    try:
        df = pd.read_csv(chemin_csv, encoding='utf-8')
        df.fillna('', inplace=True)

        # Convertir les colonnes id, user_id, is_fraud en int si possible
        colonnes_int = ['id', 'user_id', 'is_fraud']
        for col in colonnes_int:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            else:
                print(f"colonne absente : {col}")

        if 'id' not in df.columns:
            df.insert(0, 'id', range(1, len(df) + 1))

        # GET - affichage avec filtres éventuels
        if 'decision' not in df.columns:
            df['decision'] = 'en_attente'

        # SAUVEGARDE DES DÉCISIONS (POST)
        if request.method == 'POST':
            for i in range(len(df)):
                suspect_id = df.at[i, 'id'] if 'id' in df.columns else i
                champ = f"decision_{suspect_id}"
                decision_form = request.POST.get(champ)
                if decision_form in ['suspect', 'legitime', 'en_attente']:
                    df.at[i, 'decision'] = decision_form

            df.to_csv(chemin_csv, index=False, encoding='utf-8')
            messages.success(request, "Décisions enregistrées avec succès.")
            return redirect('detail_test', fichier_id=fichier_id)

        # Fitres
        filtre_decision = request.GET.get('decision')
        filtre_date = request.GET.get('date')

        if filtre_decision and filtre_decision != '':
            df = df[df['decision'] == filtre_decision]

        suspects = df.to_dict(orient='records')

        # if 'username_y' in df.columns and 'matricule_y' in df.columns:
            # username_col = 'username_y'
            # matricule_col = 'matricule_y'
        # else:
            # username_col = 'username'
            # matricule_col = 'matricule'

        
        return render(request, 'gestionnaire/detail_test.html', {
            'fichier': fichier,
            'suspects': suspects,
            'filtre_decision': filtre_decision,
            'filtre_date': filtre_date,
            # 'username_col': username_col,
            # 'matricule_col': matricule_col,
            'message': "Aperçu CSV chargé avec succès"
        })
    except Exception as e:
        return render(request, 'gestionnaire/detail_test.html', {
            'fichier': fichier,
            'erreur': f"Erreur lors du chargement du fichier : {str(e)}"
        })




# VUE GENERER RAPPORT ---------------------------------
@login_required
def generer_rapport_test_pdf(request, fichier_id):
    try:
        # Récupérer l'objet FichierSuspectsTest
        fichier = get_object_or_404(FichierSuspectsTest, id=fichier_id)
        test = fichier.campagne_test

        # Construire le chemin complet vers le fichier CSV
        chemin_csv = os.path.join(settings.MEDIA_ROOT, test.fichier_suspects_temp.name)

        # Charger les données depuis le CSV
        df = pd.read_csv(chemin_csv, encoding='utf-8')
        df.fillna('', inplace=True)

        df['is_fraud'] = df['is_fraud'].apply(lambda x: True if str(x).strip() in ['1', True] else False)

        suspects = df.to_dict(orient='records')

        template = get_template("gestionnaire/rapport_test_pdf.html")
        html = template.render({
            'fichier': fichier,
            'test': test,
            'nom_modele': test.modele.nom if test.modele else '',
            'nom_dataset': test.dataset.nom if test.dataset else '',
            'date_test': test.date_test.strftime("%d/%m/%Y") if test.date_test else '',
            'suspects': suspects,
        })

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_test_{fichier.id}.pdf"'
        pisa.CreatePDF(html, dest=response)
        return response

    except Exception as e:
        return HttpResponse(f"Erreur lors de la génération du rapport : {str(e)}")


# VUE SUPPRIMER UN FICHIER D'UN TEST
def supprimer_liste_test(request, fichier_id):
    fichier = get_object_or_404(FichierSuspectsTest, id=fichier_id)

    # Supprimer le fichier CSV du dossier
    chemin_fichier = os.path.join(settings.MEDIA_ROOT, 'suspects_temp', fichier.nom_fichier)
    if os.path.exists(chemin_fichier):
        os.remove(chemin_fichier)
        print(f">>> Fichier supprimé du disque : {chemin_fichier}")
    else:
        print(f"!!! Fichier introuvable sur le disque : {chemin_fichier}")

    # Supprimer l’entrée dans la base de données
    fichier.delete()
    messages.success(request, "Fichier des suspects supprimé avec succès.")

    return redirect('dashboard_gestionnaire')

# VUE POUR SUPPRIMER UN RESULTAT TEST
@login_required
def supprimer_campagne_test(request, test_id):
    test = get_object_or_404(CampagneTest, id=test_id)

    # Supprimer le fichier CSV du dossier
    if test.fichier_fraude and os.path.exists(test.fichier_fraude.path):
        try:
            chemin_fichier = test.fichier_fraude.path
            os.remove(chemin_fichier)
            print(f">>> Fichier supprimé du disque : {chemin_fichier}")
        except Exception as e:
            print(">>> erreur supp fichier :", str(e))
    else:
        print(f"!!! Fichier introuvable sur le disque ou non défini.")

    # Supprimer l’entrée dans la base de données
    test.delete()
    messages.success(request, "Fichier des suspects supprimé avec succès.")

    return redirect('liste_campagne_test')


# 3. ------------------------------------------- VUE POUR DASHBOARD CAMAPGNE --------------------------------------------------------------
# Lancer une campagne
@login_required
def lancer_campagne(request):
    modeles = ModeleML.objects.all()
    datasets = Dataset.objects.filter(type='nettoye')

    if request.method == 'POST':
        modele_id = request.POST.get('modeles')
        dataset_id = request.POST.getlist('datasets')
        frequence = request.POST.get('frequence') or None
        repetition = request.POST.get('repetition') or None

        modele = ModeleML.objects.get(id=modele_id)
        datasets_selected = Dataset.objects.filter(id=dataset_id)

        # Créer campagne
        campagne = Campagne.objects.create(
            modele_ml=modele,
            frequence=frequence,
            repetition=repetition,
            statut='en_attente',
            utilisateur=request.user  # Celui qui a lancé
        )
        campagne.datasets.set(datasets_selected)


        # Charger dataset principal (le premier pour l'exemple simple)
        df = pd.read_csv(datasets_selected[0].fichier.path)
        X = df.select_dtypes(include=['int64', 'float64'])

        # Charger modèle ML
        with open(modele.fichier_modele.path, "rb") as f:
            pipeline = pickle.load(f)

        # Prédictions
        predictions = pipeline.predict(X)

        # Création suspects à partir des prédictions
        suspects = []
        for i, prediction in enumerate(predictions):
            suspect = SuspectTest(
                email=f"user{i}@auto.com",
                nom=f"User {i}",
                matricule=f"{i}",
                description="Normal" if prediction == 0 else "Fraude détectée",
                decision="en_attente"
            )
            suspects.append(suspect)

        # Création du gestionnaire de risque lié à la campagne
        gestionnaire = GestionnaireRisque.objects.create(campagne=campagne)

        for s in suspects:
            s.campagne = gestionnaire
            s.save()

        # Génération du rapport automatiquement
        gestionnaire.generer_rapport_fraude(suspects)

        # Redirection après traitement
        messages.success(request, "La campagne a ete lancee avec succes.")
        return redirect('detail_campagne', campagne_id=campagne.id)
    else:
        modeles = ModeleML.objects.all()
        datasets = Dataset.objects.all()
        return render(request, "campagne/lancer_campagne.html", {"modeles": modeles, "datasets": datasets})

# Liste des campagnes + Graphiques
def liste_campagnes(request):
    # Filtres par algo et dates
    algo = request.GET.get('algo')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    campagnes = Campagne.objects.all()

    if algo:
        campagnes = campagnes.filter(modele_ml__nom=algo)

    if date_debut and date_fin:
        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d')
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d')
            campagnes = campagnes.filter(date_debut_c__range=(date_debut_obj, date_fin_obj))
        except ValueError:
            pass  # Ignore les erreurs de format

    # Statistiques par statut
    statuts_count = campagnes.values('statut').annotate(total=Count('id'))
    statuts_labels = [entry['statut'] for entry in statuts_count]
    statuts_data = [entry['total'] for entry in statuts_count]

    # Statistiques par algorithme
    algos_count = campagnes.values('modele_ml__nom').annotate(total=Count('id'))
    algos_labels = [entry['modele_ml__nom'] for entry in algos_count]
    algos_data = [entry['total'] for entry in algos_count]

    # Statistiques par fréquence
    freq_count = campagnes.values('frequence').annotate(total=Count('id')).order_by('frequence')
    freq_labels = [entry['frequence'] for entry in freq_count]
    freq_data = [entry['total'] for entry in freq_count]

    # Progression mensuelle
    mois_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    campagnes_par_mois = [0] * 12

    for campagne in campagnes:
        mois = campagne.date_debut_c.month
        campagnes_par_mois[mois - 1] += 1

    # Tous les algorithmes pour le filtre
    algos = Campagne.objects.values_list('modele_ml__nom', flat=True).distinct()

    context = {
        'campagnes': campagnes,
        'algos': algos,
        'selected_algo': algo,
        'date_debut': date_debut,
        'date_fin': date_fin,

        'statuts_labels': json.dumps(statuts_labels),
        'statuts_data': json.dumps(statuts_data),

        'algos_labels': json.dumps(algos_labels),
        'algos_data': json.dumps(algos_data),

        'frequences_labels': json.dumps(freq_labels),
        'frequences_data': json.dumps(freq_data),

        'mois_labels': json.dumps(mois_labels),
        'campagnes_par_mois': json.dumps(campagnes_par_mois),
    }

    return render(request, 'campagne/liste_campagnes.html', context)

# Démarrer une campagne
@login_required
def demarrer_campagne(request, campagne_id):
    campagne = get_object_or_404(Campagne, id=campagne_id)
    if campagne.statut == 'en_attente':
        campagne.statut = 'en_cours'
        campagne.date_debut_c = timezone.now()
        campagne.save()
    return redirect("detail_campagne", campagne_id=campagne.id)

# Suspendre une campagne
@login_required
def suspendre_campagne(request, campagne_id):
    campagne = get_object_or_404(Campagne, id=campagne_id)
    if campagne.statut == 'en_cours':
        campagne.statut = 'suspendue'
        campagne.save()
        messages.success(request, "Campagne suspendue.")
    return redirect("detail_campagne", campagne_id=campagne.id)

# Arrêter une campagne
@login_required
def arreter_campagne(request, campagne_id):
    campagne = get_object_or_404(Campagne, id=campagne_id)
    if campagne.statut in ['en_cours', 'suspendue']:
        campagne.statut = 'terminee'
        campagne.date_debut_c = timezone.now()
        campagne.save()
        messages.success(request, "Campagne arretee.")
    return redirect("detail_campagne", campagne_id=campagne.id)

# Reprendre une campagne suspendue
@login_required
def reprendre_campagne(request, campagne_id):
    campagne = get_object_or_404(Campagne, id=campagne_id)
    if campagne.statut == 'suspendue':
        campagne.statut = 'en_cours'
        campagne.date_debut_c = timezone.now()
        campagne.save()
        messages.success(request, "Campagne arretee.")
    return redirect("detail_campagne", campagne_id)


#Notification
# VUE notifications pour campagnes
@login_required
def liste_notifications(request):
    notifications = Notification.objects.filter(message__icontains="campagne")
    return render(request, 'campagne/liste_notifications.html', {'notifications': notifications})

# Detail campagne
@login_required
def detail_campagne(request, campagne_id):
    campagne = get_object_or_404(Campagne, id=campagne_id)
    rapports = GestionnaireRisque.objects.filter(campagne=campagne)
    suspects = SuspectTest.objects.filter(campagne=campagne)

    return render(request, 'campagne/detail_campagne.html', {
        'campagne': campagne,
        'rapports': rapports,
        'suspects': suspects,
    })

# 4. -----------------------------------VUE POUR LE DASHBOARD Gestionnaire Risque ----------------------------------------------------

# Accueil gestionnaire
@login_required
def dashboard_gestionnaire(request):
    # Suspects détectés
    suspects = SuspectTest.objects.all()

    # Règles métiers
    regles = RegleMetier.objects.all()

    # Dernière campagne pour le lien d’export PDF
    fichiers_suspects = FichierSuspectsTest.objects.all().order_by('-date_enregistrement')
    # Expoer CSV des suspects
    

    # Statistiques pour le graphique (répartition des décisions)
    nb_bloques = suspects.filter(decision='bloque').count()
    nb_legitimes = suspects.filter(decision='legitime').count()
    nb_attente = suspects.filter(decision='en_attente').count()

    decision_data = [nb_bloques, nb_legitimes, nb_attente]
    decision_labels = ['Bloqués', 'Légitimes', 'En attente']

    return render(request, 'gestionnaire/dashboard_gestionnaire.html', {
        'suspects': suspects,
        'regles': regles,
        'fichiers_suspects': fichiers_suspects,
        'decision_data': decision_data,
        'decision_labels': decision_labels,
    })

#bloquer suspect
@login_required
def bloquer_suspect(request, suspect_id):
    suspect = get_object_or_404(SuspectTest, id=suspect_id)
    suspect.decision = 'bloque'
    suspect.save()
    return redirect('gestionnaire/dashboard_gestionnaire')

#suspect legitime
@login_required
def legitimer_suspect(request, suspect_id):
    suspect = get_object_or_404(SuspectTest, id=suspect_id)
    suspect.decision = 'legitime'
    suspect.save()
    return redirect('gestionnaire/dashboard_gestionnaire')

# suspect en attente
@login_required
def attente_suspect(request, suspect_id):
    suspect = get_object_or_404(SuspectTest, id=suspect_id)
    suspect.decision = 'en_attente'
    suspect.save()
    return redirect('gestionnaire/dashboard_gestionnaire')


# Liste campagnes
@login_required
def gestionnaire_campagnes(request):
    campagnes = Campagne.objects.all()

    # Filtrage par statut
    statut = request.GET.get('statut')
    if statut:
        campagnes = campagnes.filter(statut=statut)

    # Filtrage par date de début (en supposant le champ s'appelle date_debut_c)
    date = request.GET.get('date')
    if date:
        campagnes = campagnes.filter(date_debut_c=date)

    return render(request, 'gestionnaire/gestionnaire_campagne.html', {
        'campagnes': campagnes
    })

# Voir rapport
@login_required
def gestion_rapport_detail(request, campagne_id):
    rapport = get_object_or_404 (GestionnaireRisque, campagne__id=campagne_id)
    campagne = rapport.campagne
    return render(request, 'gestionnaire/gestionnaire_rapport_detail.html', {
        'campagne': campagne,
        'rapport': rapport
    })

# Liste suspects d'une campagne
@login_required
def gestionnaire_suspects(request, campagne_id):
    suspects = SuspectTest.objects.filter(campagne_id=campagne_id)
    return render(request, "gestionnaire/gestionnaire_suspects.html", {"suspects": suspects, "campagne_id": campagne_id})

# Prendre décision sur un suspect
@login_required
def prendre_decision_suspect(request, suspect_id):
    suspect = get_object_or_404(SuspectTest, id=suspect_id)
    if request.method == "POST":
        decision = request.POST.get('decision')
        suspect.decision = decision
        suspect.save()
        return redirect("gestionnaire_suspects", campagne_id=suspect.campagne_id)
    return render(request, "gestionnaire/prendre_decision.html", {"suspect": suspect})

# Liste des règles métiers
@login_required
def gestionnaire_regles_metier(request):
    regles = RegleMetier.objects.all()
    return render(request, "gestionnaire/gestionnaire_regles_metier.html", {"regles": regles})

# Activer/Désactiver une règle
@login_required
def toggle_regle_metier(request, regle_id):
    regle = get_object_or_404(RegleMetier, id=regle_id)
    if request.method == 'POST':
        regle.actif = not regle.actif
        regle.save()
        return redirect("gestionnaire_regles_metier")
    return render(request, 'gestionnaire/toogle_regle_metier.html', {'regle': regle})

# Ajouter une regle
@login_required
def ajouter_regles_metier(request):
    if request.method == "POST":
        nom = request.POST.get("nom")
        description = request.POST.get("description")
        condition = request.POST.get("condition")

        RegleMetier.objects.create(
            nom=nom,
            description=description,
            condition=condition,
            actif=True
        )
        return redirect("gestionnaire_regles_metier")
    return render(request, "gestionnaire/ajouter_regles_metier.html")

# Modifier une regle
@login_required
def modifier_regles_metier(request, regle_id):
    regle = get_object_or_404(RegleMetier, id=regle_id)

    if request.method == "POST":
        regle.nom = request.POST.get("nom")
        regle.description = request.POST.get("description")
        regle.condition = request.POST.get("condition")
        regle.save()
        return redirect("gestionnaire_regles_metier")

    return render(request, "gestionnaire/modifier_regles_metier.html", {"regle": regle})

# Supprimer regle
@login_required
def supprimer_regles_metier(request, regle_id):
    regle = get_object_or_404(RegleMetier, id=regle_id)

    if request.method == "POST":
        regle.delete()
        return redirect("gestionnaire_regles_metier")

    return render(request, "gestionnaire/supprimer_regles_metier.html", {"regle": regle})

# rapport

@login_required
def rapport_campagne(request, campagne_id):
    rapport = get_object_or_404(GestionnaireRisque, campagne_id=campagne_id)
    campagne = rapport.campagne
    suspects = SuspectTest.objects.filter(campagne=campagne)
    now = timezone.now()

    return render(request, 'gestionnaire/rapport.html', {
        'rapport': rapport,
        'campagne': campagne,
        'suspects': suspects,
        'now': now
    })

#exporter rapport
@login_required
def exporter_rapport_pdf(request, campagne_id):
    # Récupérer l’objet du rapport (GestionnaireRisque lié à la campagne)
    rapport_obj = get_object_or_404(GestionnaireRisque, campagne_id=campagne_id)
    campagne = rapport_obj.campagne

    # Récupérer les suspects liés à la campagne
    suspects = SuspectTest.objects.filter(campagne=campagne)

    # Préparer la date actuelle
    now = timezone.now()

    # Contexte à passer au template
    context = {
        'rapport': rapport_obj,
        'campagne': campagne,
        'suspects': suspects,
        'now': now
    }

    # Préparer le rendu HTML
    template = get_template('rapport.html')
    html = template.render(context)

    # Réponse HTTP pour téléchargement PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_campagne_{campagne.id}.pdf"'

    # Générer le PDF via xhtml2pdf
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF', status=500)

    return response


# Notifications
# VUE notifications pour gestionnaire de risque
@login_required
def gestionnaire_notifications(request):
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    notifications = Notification.objects.filter(message__icontains="suspect")

    if date_debut:
        notifications = notifications.filter(date_creation__gte=date_debut)
    if date_fin:
        notifications = notifications.filter(date_creation__lte=date_fin)

    notifications = notifications.order_by('-date_creation')

    return render(request, 'gestionnaire/gestionnaire_notifications.html', {
        'notifications': notifications,
        'date_debut': date_debut,
        'date_fin': date_fin
    })

# 3.----------------------------- VUE POUR DASHBOARD UTILISATEUR---------------------------------------

# ----------------------
# AUTHENTIFICATION
# -----------------------
def connexion_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            identifiant = form.cleaned_data["identifiant"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=identifiant, password=password)

        if user is not None:
            login(request, user)
            if user.role == 'admin':
                return redirect('dashboard_admin')
            elif user.role == 'analyste':
                return redirect('dashboard_analyste')
            else:
                messages.error(request, "Role non reconnu")
                return redirect('login')
        else:
            messages.error(request, "Identifiants invalides.")
            return redirect('login')
    else:
        form = LoginForm()

    return render(request, "login.html", {'form': form})

@login_required
def deconnexion_view(request):
    logout(request)
    return redirect('login')




# -----------------------
# GESTION UTILISATEURS (Admin uniquement)
# -----------------------
@admin_required
def liste_utilisateurs(request):
    # Recuperation du filtre de role
    role_filter = request.GET.get('role', '')
    
    # Filtrage des utilisateurs selon le role
    if role_filter:
        utilisateurs = Utilisateur.objects.filter(role=role_filter)
    else:
        utilisateurs = Utilisateur.objects.all()

    # Statistique pour l'affichage et le graphique
    admins_count = Utilisateur.objects.filter(role='admin').count()
    analystes_count = Utilisateur.objects.filter(role='analyste').count()

    # Donnees du graphique
    chart_labels = ['Admins', 'Analystes']
    chart_data = [admins_count, analystes_count]

    context = {
        'utilisateurs': utilisateurs,
        'role_filter': role_filter,
        'admins_count': admins_count,
        'analystes_count': analystes_count,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'utilisateur/liste_utilisateurs.html', context)

#ajouter un user
from .forms import AjouterUtilisateurForm

@admin_required
def ajouter_utilisateur(request):
    if request.method == 'POST':
        form = AjouterUtilisateurForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur ajouté avec succès.")
            return redirect('liste_utilisateurs')
    else:
        form = AjouterUtilisateurForm()
    
    return render(request, 'utilisateur/ajouter_utilisateur.html', {'form': form})


# Modifier un user
from .forms import UtilisateurModificationForm

@admin_required
def modifier_utilisateur(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)

    if request.method == 'POST':
        form = UtilisateurModificationForm(request.POST, instance=utilisateur)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur modifié avec succès.")
            return redirect('liste_utilisateurs')
    else:
        form = UtilisateurModificationForm(instance=utilisateur)

    return render(request, 'utilisateur/modifier_utilisateur.html', {'form': form, 'utilisateur': utilisateur})

#Supprimer un user
@admin_required
def supprimer_utilisateur(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)

    if request.method == 'POST':
        utilisateur.delete()
        messages.success(request, "Utilisateur supprimé avec succès.")
        return redirect('liste_utilisateurs')

    return render(request, 'utilisateur/supprimer_utilisateur.html', {'utilisateur': utilisateur})