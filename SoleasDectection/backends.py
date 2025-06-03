#pour permettre a l'utilisateur de se connecter soit par mail ou nom

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentifie avec email ou username.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get("username") or kwargs.get("identifiant") or kwargs.get("email")

        if not username:
            return None

        user = None

        try:
            # Vérifie si c'est un email
            if '@' in username:
                user = User.objects.get(email=username)
            else:
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None