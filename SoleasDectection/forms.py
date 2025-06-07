from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
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
from django import forms
from .models import Utilisateur

class UtilisateurCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirmer le mot de passe")

    class Meta:
        model = Utilisateur
        fields = ['email', 'nom', 'password', 'password_confirm', 'role']

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get("password")
        confirm = cleaned_data.get("password_confirm")
        if pwd and confirm and pwd != confirm:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

#3. ---------------------formulaire pour editer un profil
from django import forms
from django.contrib.auth.models import User

class ProfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

#2. ------------------------ formulaire ajouter utilisateur ---------------
class AjouterUtilisateurForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")

    class Meta:
        model = Utilisateur
        fields = ['nom', 'email', 'role', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


# ---------------------------- formulaire pour modifier un user
class UtilisateurModificationForm(UserChangeForm):
    password = None  # On masque le champ mot de passe

    class Meta:
        model = Utilisateur
        fields = ['email', 'nom', 'role', 'is_active']

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