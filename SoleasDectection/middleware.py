from django.shortcuts import redirect

class OTPVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Liste des chemins à exclure de la vérification OTP
        EXEMPT_URLS = [
            '/login/',
            '/register/',
            '/otp-verification/',
            '/dashboard_accueil/',  # adapte selon ton url réelle
            '/admin/',  # optionnel
            '/',
        ]
        # Laisse passer si l'URL commence par un des chemins ci-dessus
        if request.user.is_authenticated and not getattr(request.user, 'otp_verified', True):
            if not any(request.path.startswith(url) for url in EXEMPT_URLS):
                return redirect('otp_verification')
        return self.get_response(request)