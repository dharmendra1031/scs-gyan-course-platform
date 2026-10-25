from django.contrib.auth import views as auth_views
from .auth_views import ManagementAwareLoginView
from django.urls import path

from . import views
from .password_reset import RecoveryRequest, RecoverySent, RecoveryConfirm, RecoveryComplete

urlpatterns = [
    path("login/", ManagementAwareLoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password-reset/", RecoveryRequest.as_view(), name="password_reset"),
    path("password-reset/sent/", RecoverySent.as_view(), name="password_reset_done"),
    path("password-reset/confirm/<uidb64>/<token>/", RecoveryConfirm.as_view(), name="password_reset_confirm"),
    path("password-reset/complete/", RecoveryComplete.as_view(), name="password_reset_complete"),
    path("signup/", views.signup, name="signup"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("notifications/", views.notification_inbox, name="notification_inbox"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="notification_read"),
]
