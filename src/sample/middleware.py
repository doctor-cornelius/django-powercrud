"""Sample-project middleware helpers."""

from django.contrib.auth import get_user_model, login


class AutoLoginSampleUserMiddleware:
    """Auto-login a stable demo user for the sample app in local development."""

    demo_username = "sample-demo"
    demo_email = "sample-demo@example.com"

    def __init__(self, get_response):
        """Store the downstream middleware callable."""

        self.get_response = get_response

    def __call__(self, request):
        """Ensure sample routes run with a predictable authenticated demo user."""

        if request.path.startswith("/sample/") and not request.user.is_authenticated:
            user_model = get_user_model()
            user, _created = user_model.objects.get_or_create(
                username=self.demo_username,
                defaults={"email": self.demo_email},
            )
            backend_path = "django.contrib.auth.backends.ModelBackend"
            user.backend = backend_path
            login(request, user, backend=backend_path)

        return self.get_response(request)
