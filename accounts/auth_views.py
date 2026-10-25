from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy


class ManagementAwareLoginView(LoginView):
    def get_default_redirect_url(self):
        if self.request.user.is_superuser:
            return str(reverse_lazy("management:dashboard"))
        return str(reverse_lazy("dashboard"))
