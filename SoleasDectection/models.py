from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, User
# Create your models here.
# 1. -------------------- Table Dataset ---------------------------------
class Dataset(models.Model):
    TYPE_CHOICES = [
        ('brut', 'Fichier brut'),
        ('nettoye', 'Fichier nettoye'),
    ]

    FORMAT_CHOICES =[
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]
    nom = models.CharField(max_length=100)
    description = models.TextField()
    dateC = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES, default='brut') 
    format_fichier = models.CharField(max_length=50, choices=FORMAT_CHOICES, default='csv') 
    fichier = models.FileField(upload_to='datasets/')
    

    # affiche le nom du dataset et le type
    def __str__(self):
        return f"{self.nom} ({self.type})"

# 2. ----------------------- 2. Table ModeleMl ---------------------------------
class ModeleML(models.Model):
    ALGORITHME_CHOICES = [
        ('isolation_forest', 'Isolation Forest'),
        ('svm', 'SVM'),
        ('kmeans', 'K-Means'),
    ]

    FRAUDE_CHOICES = [
        ('cartes', 'Cartes virtuelles'),
        ('transactions', 'Transactions'),
    ]

    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    algorithme = models.CharField(max_length=50, choices=ALGORITHME_CHOICES)
    type_fraude = models.CharField(max_length=50, choices=FRAUDE_CHOICES)
    fichier_modele = models.FileField(upload_to='modeles_ml/', blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.nom} ({self.algorithme} - {self.type_fraude})"


# 4. --------------------- Table Campagne + Notification ----------------------------------------------------------
class Campagne(models.Model):
    STATUTS = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('suspendue', 'Suspendue'),
    ]

    FREQUENCES = [
        ('quotidien', 'Chaque jour'),
        ('hebdomadaire', 'Chaque semaine'),
        ('bihebdomadaire', 'Deux fois par semaine'),
        ('mensuel', 'Chaque mois'),
    ]

    REPETITIONS = [
        ('1h', 'Toutes les 1 heure'),
        ('6h', 'Toutes les 6 heures'),
        ('12h', 'Toutes les 12 heures'),
        ('24h', 'Toutes les 24 heures'),
    ]

    # Champs principaux
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    frequence = models.CharField(max_length=20, choices=FREQUENCES)
    repetition = models.CharField(max_length=10, choices=REPETITIONS, null=True, blank=True)
    date_debut_c = models.DateTimeField(default=timezone.now)
    date_fin_c = models.DateTimeField(null=True, blank=True)

    utilisateur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='campagnes')
    modele_ml = models.ForeignKey('ModeleML', on_delete=models.CASCADE, related_name='campagnes')
    datasets = models.ManyToManyField('Dataset', related_name='campagnes')

    def demarrer_campagne(self):
        self.statut = 'en_cours'
        self.date_debut_c = timezone.now()
        self.save()

    def suspendre_campagne(self):
        self.statut = 'suspendue'
        self.save()

    def arreter_campagne(self):
        self.statut = 'terminee'
        self.date_fin_c = timezone.now()
        self.save()

    # afficher numero campagne - status - frequence - repetition
    def _str_(self):
        return f"Campagne #{self.id} - {self.get_statut_display()} - {self.frequence} / {self.repetition}"



class Notification(models.Model):
    titre = models.CharField(max_length=255)
    message = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    def _str_(self):
        return f"{self.titre} - {self.date_creation.strftime('%Y-%m-%d %H:%M:%S')}"

# 5. --------------------------- Table Gestionnaire risque ---------------------------------------------------------------------------

# ----------------------
# GestionnaireRisque
# ----------------------

class GestionnaireRisque(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    campagne = models.ForeignKey("Campagne", on_delete=models.CASCADE, related_name='rapports')
    rapport = models.TextField(blank=True, null=True)

    def generer_rapport_fraude(self, suspects):
        contenu = "===== RAPPORT DE FRAUDE DE LA CAMPAGNE =====\n\n"

        for s in suspects:
            contenu += f"Email : {s.email}\n"
            contenu += f"Nom : {s.nom}\n"
            contenu += f"Matricule : {s.matricule}\n"
            contenu += f"Motif : {s.description}\n"
            contenu += f"Décision : {s.get_decision_display()}\n"
            contenu += "-" * 50 + "\n"

        self.rapport = contenu
        self.save()

        # Notifier automatiquement
        self.notifier_alerte()

    def notifier_alerte(self):
        Notification.objects.create(
            message=f"ALERTE : Suspects détectés dans la campagne {self.campagne.id}"
        )

    def _str_(self):
        return f"Rapport de la campagne {self.campagne.id}"


# ----------------------
# Suspect
# ----------------------

class Suspect(models.Model):
    campagne = models.ForeignKey(GestionnaireRisque, on_delete=models.CASCADE, related_name='suspects')
    email = models.EmailField()
    nom = models.CharField(max_length=200)
    matricule = models.CharField(max_length=100)
    description = models.TextField()

    DECISION_CHOICES = [
        ('en_attente', 'En attente'),
        ('bloque', 'Bloqué'),
        ('legitime', 'Faux positif / Légitime'),
    ]

    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default='en_attente')

    def _str_(self):
        return f"{self.nom} ({self.decision})"

# ----------------------
# Regle metier
# ----------------------

class RegleMetier(models.Model):
    nom = models.CharField(max_length=255)
    description = models.TextField()
    condition = models.TextField(help_text="Exemple : montant > 1000000")
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return self.nom

# 1. ----------------------------------- Table Utilisateur ----------------------------------------------------------------------
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

# 1. Manager personnalisé pour créer les utilisateurs et superusers
class UtilisateurManager(BaseUserManager):
    def create_user(self, email, nom, password=None, role='analyste'):
        if not email:
            raise ValueError('Un utilisateur doit avoir un email')
        email = self.normalize_email(email)
        user = self.model(email=email, nom=nom, role=role)
        user.set_password(password)  # Hash du mot de passe
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nom, password=None):
        # Crée un super administrateur
        user = self.create_user(email, nom, password, role='admin')
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

# 2. Modèle Utilisateur principal
class Utilisateur(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('analyste', 'Analyste'),
    ]

    email = models.EmailField(unique=True)  # L'email sert d'identifiant unique
    nom = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='analyste')

    # Champs nécessaires pour Django Admin
    is_active = models.BooleanField(default=True)      # Le compte est actif ou désactivé
    is_staff = models.BooleanField(default=False)      # Peut accéder à l'admin Django
    date_joined = models.DateTimeField(default=timezone.now)  # Date d'inscription

    # Lien avec notre Manager
    objects = UtilisateurManager()

    # Définir quel champ sera utilisé pour se connecter
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom']  # Champs demandés en plus lors de la création superuser

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def _str_(self):
        return f"{self.nom} ({self.email})"

    # Petite propriété utile pour vérifier rapidement si l'utilisateur est admin
    @property
    def is_admin(self):
        return self.role == 'admin'