from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import models
from .forms import UtilisateurCreationForm
from django.forms import Textarea
from .models import Utilisateur, Dataset, ModeleML, Campagne, Notification,GestionnaireRisque, RegleMetier, CampagneTest, SuspectTest, FichierSuspectsTest

# 1. ----------------------------------------------------------------
@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    add_form = UtilisateurCreationForm
    model = Utilisateur
    list_display = ('email', 'nom', 'role', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'nom')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'nom', 'password')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('date_joined',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nom', 'role', 'password1', 'password2', 'is_active', 'is_staff')}
        ),
    )

# 2.--------------------------------------------------------------
@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description', 'type', 'fichier', 'fichier_brut', 'dateC', 'format_fichier')
    search_fields = ('nom', 'description')
    list_filter = ('type', 'fichier', 'fichier_brut')

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 40})},
    }

    def format_fichier(self, obj):
        if obj.fichier and '.' in obj.fichier.name:
            return obj.fichier.name.split('.')[-1].upper()
        return "Aucun"
    format_fichier.short_description = "Format"

# 3. ----------------------------------------------------------------
@admin.register(ModeleML)
class ModeleMLAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description', 'algorithme', 'type_fraude', 'fichier_modele', 'date_creation')
    search_fields = ('nom', 'description')
    list_filter = ('algorithme', 'type_fraude')

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 40})},
    }

# 4. --------------------------------------------------------------
@admin.register(Campagne)
class CampagneAdmin(admin.ModelAdmin):
    list_display = ('id', 'statut', 'frequence', 'repetition', 'date_debut_c', 'date_fin_c')
    search_fields = ('id',)
    list_filter = ('statut', 'frequence', 'repetition')
    readonly_fields = ('date_debut_c', 'date_fin_c')

    # Affichage formaté (facultatif pour customiser les dates)
    def date_debut(self, obj):
        return obj.date_debut_c.strftime('%Y-%m-%d %H:%M') if obj.date_debut_c else "-"
    date_debut.short_description = "Début"

    def date_fin(self, obj):
        return obj.date_fin_c.strftime('%Y-%m-%d %H:%M') if obj.date_fin_c else "-"
    date_fin.short_description = "Fin"

# 5. ----------------------------------------------------------
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'titre', 'date_creation', 'utilisateur')
    search_fields = ('titre',)
    list_filter = ('date_creation', 'utilisateur')
    readonly_fields = ('date_creation',)

# 6. -----------------------------------------------------------
@admin.register(GestionnaireRisque)
class GestionnaireRisqueAdmin(admin.ModelAdmin):
    list_display = ('id', 'campagne', 'campagne_test', 'date')
    search_fields = ('campagne__id', 'campagne_test__id')
    list_filter = ('date', 'campagne', 'campagne_test')
    readonly_fields = ('date',)
# 7. ------------------------------------------------------------------

# 8. ----------------------------------------------------------------------
@admin.register(RegleMetier)
class RegleMetierAdmin(admin.ModelAdmin):
    list_display = ('nom', 'actif', 'date_creation')
    search_fields = ('nom', 'description', 'condition')
    list_filter = ('actif', 'date_creation')
    formfield_overrides = {
        models.TextField: {'widget': admin.widgets.AdminTextareaWidget(attrs={'rows': 2, 'cols': 40})},
    }

@admin.register(CampagneTest)
class CampagneTestAdmin(admin.ModelAdmin):
    list_display = ('id', 'modele', 'dataset', 'statut', 'date_test',)
    list_filter = ('statut', 'date_test')
    search_fields = ('modele__nom', 'dataset__nom')
    date_hierarchy = 'date_test'
    ordering = ('-date_test',)


@admin.register(SuspectTest)
class SuspectTestAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'matricule', 'description', 'campagne_test')
    list_filter = ('campagne_test',)
    search_fields = ('username', 'matricule', 'description')
    ordering = ('-user_id',)


#______________________ fichier test ------------------------------------
from .models import FichierSuspectsTest

@admin.register(FichierSuspectsTest)
class FichierSuspectsTestAdmin(admin.ModelAdmin):
    list_display = ['campagne_test', 'nom_fichier', 'date_enregistrement']
    list_filter = ['date_enregistrement']

    