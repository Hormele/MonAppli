from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.db.models import Count
from collections import Counter
from django.template.loader import get_template
from xhtml2pdf import pisa
from .forms import LoginForm
from .models import Campagne, Utilisateur, Dataset, GestionnaireRisque, Suspect, Notification, ModeleML, Suspect, RegleMetier, Campagne
from .services.train_model import entrainer_modele
from django.contrib import messages
import pandas as pd
import pickle
import os, json


def admin_required(view_func):
    decorated_view_func = user_passes_test(lambda u: u.is_authenticated and u.role == 'admin')(view_func)
    return decorated_view_func

Utilisateur = get_user_model()

#1.-------------------- VUE POUR LE DASHBOARD D'ACCEUIL----------------------
def dashboard_accueil(request):
    return render(request, 'dashboard_accueil.html')

#-------------------------- VUE DASHBOARD ADMIN 
@login_required
def dashboard_admin(request):
    datasets_count = Dataset.objects.count()
    modeles_count = ModeleML.objects.count()
    campagnes_count = Campagne.objects.count()
    rapports_count = GestionnaireRisque.objects.exclude(rapport="").count()
    users_count = Utilisateur.objects.count()
    admins_count = Utilisateur.objects.filter(role='admin').count()
    analystes_count = Utilisateur.objects.filter(role='analyste').count()

    return render(request, 'dashboard_admin.html', {
        'datasets_count': datasets_count,
        'modeles_count': modeles_count,
        'campagnes_count': campagnes_count,
        'rapports_count': rapports_count,
        'users_count': users_count,
        'admins_count': admins_count,
        'analystes_count': analystes_count,
    })

#-------------------------------- VUE DASHBOARD ANALYSTE -----------------------
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Campagne, GestionnaireRisque

@login_required
def dashboard_analyste(request):
    campagnes_en_cours = Campagne.objects.filter(statut='en_cours').count()
    campagnes_terminees = Campagne.objects.filter(statut='terminée').count()

    suspects_legitime = GestionnaireRisque.objects.filter(decision='légitime').count()
    suspects_bloque = GestionnaireRisque.objects.filter(decision='bloqué').count()
    suspects_attente = GestionnaireRisque.objects.filter(decision='en_attente').count()

    context = {
        'campagnes_en_cours': campagnes_en_cours,
        'campagnes_terminees': campagnes_terminees,
        'suspects_legitime': suspects_legitime,
        'suspects_bloque': suspects_bloque,
        'suspects_attente': suspects_attente,
    }
    return render(request, 'utilisateur/dashboard_analyste.html', context)

#------------------------- VUE POUR ABOUT----------------
def about(request):
    return render(request, 'about.html')

#---------------------------- VUE POUR contact
def contact(request):
    return render(request, 'contact.html')

#2. ----------------------- VUE DASHBOARD DATASET ----------------------------------------------------------------------------


#2-1. VUE POUR Liste des datasets + Statistiques -------------
def liste_datasets(request):
    type_filter = request.GET.get('type')
    format_filter = request.GET.get('format')

    datasets = Dataset.objects.all()

    if type_filter:
        datasets = datasets.filter(type=type_filter)

    if format_filter:
        datasets = datasets.filter(fichier__icontains=format_filter)

    brut_count = Dataset.objects.filter(type='brut').count()
    nettoye_count = Dataset.objects.filter(type='nettoye').count()

    return render(request, 'dataset/liste_datasets.html', {
        'datasets': datasets,
        'brut_count': brut_count,
        'nettoye_count': nettoye_count,
    })

#2-2. VUE POUR Uploader un dataset--------------------
@login_required
def uploader_dataset(request):
    if request.method == "POST":
        nom = request.POST.get("nom")
        description = request.POST.get("description")
        type_fichier = request.POST.get("type")
        fichier = request.FILES.get("fichier")

        Dataset.objects.create(
            nom=nom,
            description=description,
            type=type_fichier,
            fichier=fichier,
            format_fichier="csv"  # Automatisable si besoin
        )

        return redirect("liste_datasets")

    return render(request, "uploader_dataset.html")

#2-3. VUE POUR Supprimer un dataset ----------------------
@login_required
def supprimer_dataset(request, dataset_id):
    dataset = Dataset.objects.get(id=dataset_id)

    if dataset.fichier and os.path.exists(dataset.fichier.path):
        os.remove(dataset.fichier.path)

    dataset.delete()
    return redirect("liste_datasets")

#3.----------------------------------------- VUE POUR  Dashboard ModelML-----------------------------------------------------------------

#1. VUE POUR LISTER LES MODELES + Statistiques -----------
@login_required
def liste_modeles(request):
    algo_filtre = request.GET.get('algo', '')
    if algo_filtre:
        modeles = ModeleML.objects.filter(algorithme=algo_filtre)
    else:
        modeles = ModeleML.objects.all()

    # Statistiques
    algo_labels = list(ModeleML.objects.values_list('algorithme', flat=True).distinct())
    algo_data = [ModeleML.objects.filter(algorithme=algo).count() for algo in algo_labels]

    fraude_labels = list(ModeleML.objects.values_list('type_fraude', flat=True).distinct())
    fraude_data = [ModeleML.objects.filter(type_fraude=fraude).count() for fraude in fraude_labels]

    return render(request, 'liste_modeles.html', {
        'modeles': modeles,
        'algo_labels': algo_labels,
        'algo_data': algo_data,
        'fraude_labels': fraude_labels,
        'fraude_data': fraude_data,
    })


# SUPPRIMER UN MODELE
@login_required
def supprimer_modele(request, modele_id):
    modele = ModeleML.objects.get(id=modele_id)

    # Supprimer fichier
    if modele.fichier_modele and os.path.exists(modele.fichier_modele.path):
        os.remove(modele.fichier_modele.path)

    modele.delete()
    return redirect('liste_modeles')

#2. VUE POUR ENTRAINER UN MODELE----------
@login_required
def entrainer_modele_view(request):
    datasets = Dataset.objects.filter(type='nettoye')

    if request.method == "POST":
        dataset_id = request.POST.get("dataset")
        algorithme = request.POST.get("algorithme")
        type_fraude = request.POST.get("type_fraude")

        dataset = Dataset.objects.get(id=dataset_id)

        # Nom fichier modèle
        nom_fichier = f"{algorithme}_{type_fraude}.pkl"
        modele_pkl_path = os.path.join("media/modeles_ml/", nom_fichier)

        # Entraînement
        entrainer_modele(dataset.fichier.path, algorithme, modele_pkl_path, pca=True)

        # Enregistrement
        ModeleML.objects.create(
            nom=f"{algorithme} - {type_fraude}",
            description=f"Modèle entraîné sur {dataset.nom}",
            algorithme=algorithme,
            type_fraude=type_fraude,
            fichier_modele=modele_pkl_path
        )

        return redirect("liste_modeles")

    return render(request, "entrainer_modele.html", {"datasets": datasets})

#3.VUE POUR TESTER UN MODELEML SUR UN DATASET NETTOYE
@login_required
def tester_modele(request):
    modeles = ModeleML.objects.all()
    datasets = Dataset.objects.filter(type='nettoye')
    resultat = None
    graph_data = None

    if request.method == "POST":
        modele_id = request.POST.get("modele")
        dataset_id = request.POST.get("dataset")

        modele = ModeleML.objects.get(id=modele_id)
        dataset = Dataset.objects.get(id=dataset_id)

        df = pd.read_csv(dataset.fichier.path)
        X = df.select_dtypes(include=['int64', 'float64'])

        # Charger le modèle pipeline
        with open(modele.fichier_modele.path, "rb") as f:
            pipeline = pickle.load(f)

        # Prédiction
        predictions = pipeline.predict(X)

        resultat = list(predictions)

        # Statistiques pour graphique
        counter = Counter(resultat)

        graph_data = {
            "labels": ["Normal (1)", "Anomalie (-1)"],
            "data": [counter.get(1, 0), counter.get(-1, 0)]
        }

    return render(request, "tester_modele.html", {
        "modeles": modeles,
        "datasets": datasets,
        "resultat": resultat,
        "graph_data": json.dumps(graph_data) if graph_data else None
    })

# 3. ------------------------------------------- VUE POUR DASHBOARD CAMAPGNE --------------------------------------------------------------
# Lancer une campagne
@login_required
def lancer_campagne(request):
    modeles = ModeleML.objects.all()
    datasets = Dataset.objects.filter(type='nettoye')

    if request.method == "POST":
        modele_id = request.POST.get("modele")
        dataset_ids = request.POST.getlist("datasets")
        frequence = request.POST.get("frequence")
        repetition = request.POST.get("repetition")

        modele = ModeleML.objects.get(id=modele_id)
        datasets_selected = Dataset.objects.filter(id__in=dataset_ids)

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
            suspect = Suspect(
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
        return redirect("liste_campagnes")

    else:
        modeles = ModeleML.objects.all()
        datasets = Dataset.objects.all()
        return render(request, "lancer_campagne.html", {"modeles": modeles, "datasets": datasets})

# Liste des campagnes + Graphiques
from django.db.models import Count
from django.db.models.functions import TruncWeek

@login_required
def liste_campagnes(request):
    campagnes = Campagne.objects.all().order_by('-date_debut_c')

    # Statistiques par statut
    statut_data = Campagne.objects.values('statut').annotate(total=Count('id'))
    statut_labels = [item['statut'] for item in statut_data]
    statut_counts = [item['total'] for item in statut_data]

    # Statistiques par algorithme
    algo_data = Campagne.objects.values('modele_ml__algorithme').annotate(total=Count('id'))
    algo_labels = [item['modele_ml__algorithme'] for item in algo_data]
    algo_counts = [item['total'] for item in algo_data]

    # Statistiques par fréquence
    freq_data = Campagne.objects.values('frequence').annotate(total=Count('id'))
    freq_labels = [item['frequence'] for item in freq_data]
    freq_counts = [item['total'] for item in freq_data]

    # Progression par semaine
    semaine_data = Campagne.objects.annotate(semaine=TruncWeek('date_debut_c')) \
                                   .values('semaine') \
                                   .annotate(total=Count('id')) \
                                   .order_by('semaine')
    progression_labels = [item['semaine'].strftime("%d/%m") for item in semaine_data]
    progression_data = [item['total'] for item in semaine_data]

    return render(request, 'liste_campagnes.html', {
        'campagnes': campagnes,
        'statut_labels': statut_labels,
        'statut_data': statut_counts,
        'algo_labels': algo_labels,
        'algo_data': algo_counts,
        'freq_labels': freq_labels,
        'freq_data': freq_counts,
        'progression_labels': progression_labels,
        'progression_data': progression_data
    })

# Démarrer une campagne
@login_required
def demarrer_campagne(request, id):
    campagne = get_object_or_404(Campagne, id=id)
    campagne.demarrer_campagne()
    return redirect("liste_campagnes")

# Suspendre une campagne
@login_required
def suspendre_campagne(request, id):
    campagne = get_object_or_404(Campagne, id=id)
    campagne.suspendre_campagne()
    return redirect("liste_campagnes")

# Arrêter une campagne
@login_required
def arreter_campagne(request, id):
    campagne = get_object_or_404(Campagne, id=id)
    campagne.arreter_campagne()
    return redirect("liste_campagnes")

#Notification
# VUE notifications pour campagnes
@login_required
def liste_notifications(request):
    notifications = Notification.objects.filter(message__icontains="campagne")
    return render(request, 'liste_notifications.html', {'notifications': notifications})

# Detail campagne
@login_required
def detail_campagne(request, campagne_id):
    campagne = get_object_or_404(Campagne, id=campagne_id)
    rapports = GestionnaireRisque.objects.filter(campagne=campagne)
    suspects = Suspect.objects.filter(campagne=campagne)

    return render(request, 'detail_campagne.html', {
        'campagne': campagne,
        'rapports': rapports,
        'suspects': suspects,
    })

# 4. -----------------------------------VUE POUR LE DASHBOARD Gestionnaire Risque ----------------------------------------------------

# Accueil gestionnaire
@login_required
def dashboard_gestionnaire(request):
    # Suspects détectés
    suspects = Suspect.objects.all()

    # Règles métiers
    regles = RegleMetier.objects.all()

    # Dernière campagne pour le lien d’export PDF
    campagne = Campagne.objects.order_by('-date_creation').first()
    campagne_id = campagne.id if campagne else None

    # Statistiques pour le graphique (répartition des décisions)
    nb_bloques = suspects.filter(decision='bloque').count()
    nb_legitimes = suspects.filter(decision='legitime').count()
    nb_attente = suspects.filter(decision='en_attente').count()

    decision_data = [nb_bloques, nb_legitimes, nb_attente]
    decision_labels = ['Bloqués', 'Légitimes', 'En attente']

    return render(request, 'dashboard_gestionnaire.html', {
        'suspects': suspects,
        'regles': regles,
        'campagne_id': campagne_id,
        'decision_data': decision_data,
        'decision_labels': decision_labels,
    })

# Liste campagnes
@login_required
def gestionnaire_campagnes(request):
    campagnes = Campagne.objects.all()
    return render(request, "gestionnaire_campagnes.html", {"campagnes": campagnes})

# Voir rapport
@login_required
def consulter_rapport_campagne(request, campagne_id):
    rapport = GestionnaireRisque.objects.get(campagne__id=campagne_id)
    return render(request, 'gestionnaire_rapport_detail.html', {'rapport': rapport})

# Liste suspects d'une campagne
@login_required
def gestionnaire_suspects(request, campagne_id):
    suspects = Suspect.objects.filter(campagne_id=campagne_id)
    return render(request, "gestionnaire_suspects.html", {"suspects": suspects, "campagne_id": campagne_id})

# Prendre décision sur un suspect
@login_required
def prendre_decision_suspect(request, suspect_id):
    suspect = get_object_or_404(Suspect, id=suspect_id)
    if request.method == "POST":
        suspect.decision = request.POST.get("decision")
        suspect.save()
        return redirect("gestionnaire_suspects", campagne_id=suspect.campagne_id)
    return render(request, "prendre_decision.html", {"suspect": suspect})

# Liste des règles métiers
@login_required
def gestionnaire_regles_metier(request):
    regles = RegleMetier.objects.all()
    return render(request, "gestionnaire_regles_metier.html", {"regles": regles})

# Activer/Désactiver une règle
@login_required
def toggle_regle_metier(request, regle_id):
    regle = get_object_or_404(RegleMetier, id=regle_id)
    regle.active = not regle.active
    regle.save()
    return redirect("gestionnaire_regles_metier")

# Ajouter une regle
@admin_required
def ajouter_regles_metier(request):
    if request.method == "POST":
        nom = request.POST.get("nom")
        description = request.POST.get("description")
        condition = request.POST.get("condition")
        RegleMetier.objects.create(nom=nom, description=description, condition=condition)
        return redirect("gestionnaire_regles_metier")
    return render(request, "ajouter_regles_metier.html")

# Modifier une regle
@admin_required
def modifier_regles_metier(request, regle_id):
    regle = get_object_or_404(RegleMetier, id=regle_id)

    if request.method == "POST":
        regle.nom = request.POST.get("nom")
        regle.description = request.POST.get("description")
        regle.condition = request.POST.get("condition")
        regle.save()
        return redirect("gestionnaire_regles_metier")

    return render(request, "modifier_regles_metier.html", {"regle": regle})

# Supprimer regle
@login_required
def supprimer_regles_metier(request, regle_id):
    regle = get_object_or_404(RegleMetier, id=regle_id)

    if request.method == "POST":
        regle.delete()
        return redirect("gestionnaire_regles_metier")

    return render(request, "supprimer_regles_metier.html", {"regle": regle})

#exporter rapport
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

@login_required
def exporter_rapport_pdf(request, campagne_id):
    rapport_obj = GestionnaireRisque.objects.get(campagne__id=campagne_id)

    template_path = 'gestionnaire/rapport_pdf.html'
    context = {'rapport': rapport_obj}
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_campagne_{campagne_id}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF')
    return response

# Notifications
# VUE notifications pour gestionnaire de risque
@login_required
def gestionnaire_notifications(request):
    notifications = Notification.objects.filter(message__icontains="suspects")
    return render(request, 'gestionnaire_notifications.html', {'notifications': notifications})

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
    role_filter = request.GET.get('role', '')
    
    if role_filter:
        utilisateurs = Utilisateur.objects.filter(role=role_filter)
    else:
        utilisateurs = Utilisateur.objects.all()

    admins_count = Utilisateur.objects.filter(role='admin').count()
    analystes_count = Utilisateur.objects.filter(role='analyste').count()

    context = {
        'utilisateurs': utilisateurs,
        'role_filter': role_filter,
        'admins_count': admins_count,
        'analystes_count': analystes_count,
    }
    return render(request, 'utilisateur/liste_utilisateurs.html', context)

@admin_required
def ajouter_utilisateur(request):
    if request.user.role != "admin":
        return redirect('dashboard_utilisateur')

    if request.method == "POST":
        email = request.POST.get("email")
        nom = request.POST.get("nom")
        password = request.POST.get("password")
        role = request.POST.get("role")

        Utilisateur.objects.create_user(email=email, nom=nom, password=password, role=role)
        return redirect("utilisateur_utilisateurs")

    return render(request, "ajouter_utilisateur.html")


@admin_required
def modifier_utilisateur(request, user_id):
    if request.user.role != "admin":
        return redirect('dashboard_utilisateur')

    user = get_object_or_404(Utilisateur, id=user_id)

    if request.method == "POST":
        user.nom = request.POST.get("nom")
        user.email = request.POST.get("email")
        user.role = request.POST.get("role")
        user.save()
        return redirect("utilisateur_utilisateurs")

    return render(request, "modifier_utilisateur.html", {"utilisateur": user})


@admin_required
def supprimer_utilisateur(request, user_id):
    if request.user.role != "admin":
        return redirect('dashboard_utilisateur')

    user = get_object_or_404(Utilisateur, id=user_id)
    user.delete()
    return redirect("utilisateur_utilisateurs")
