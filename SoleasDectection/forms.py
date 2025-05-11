from django import forms
from django.contrib.auth.forms import UserCreationForm
from SoleasDectection.models import Campagne, Utilisateur, RegleMetier

# 1. ---------------------- formulaire pour se connecter--------------------
class LoginForm(forms.Form):
    identifiant = forms.CharField(
        label="Email ou Nom d'utilisateur",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre email ou nom'})
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Votre mot de passe'})
    )
# 2. ----------------------------
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ('email', 'nom', 'role', 'is_active', 'is_staff', 'password1', 'password2')

#2. ------------------------ formulaire ajouter utilisateur ---------------
"""class AjouterUtilisateurForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")

    class Meta:
        model = Utilisateur
        fields = ['nom', 'email', 'role', 'password']"""

#3. ---------------------- formulaire campagne ---------------
"""class CampagneForm(forms.ModelForm):
    class Meta:
        model = Campagne
        fields = ['nom', 'dataset', 'modele_ml']"""


#4. --------------------- formulaire regles metier
"""class AjouterRegleMetierForm(forms.ModelForm):
    class Meta:
        model = RegleMetier
        fields = ['nom', 'description', 'condition']"""