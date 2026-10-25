from django.conf import settings
from django.contrib.auth import views as auth_views
from django.http import Http404
from django.urls import reverse_lazy


class RecoveryGate:
    def dispatch(self, request, *args, **kwargs):
        if not settings.PASSWORD_RESET_ENABLED:
            raise Http404("Password recovery is not configured.")
        return super().dispatch(request, *args, **kwargs)


class RecoveryRequest(RecoveryGate, auth_views.PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")


class RecoverySent(RecoveryGate, auth_views.PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class RecoveryConfirm(RecoveryGate, auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class RecoveryComplete(RecoveryGate, auth_views.PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"
