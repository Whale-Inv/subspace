from django.contrib.auth.views import LogoutView
from django.urls import path

from apps.users.apps import UsersConfig
from apps.users.views import (AccountView, LoginView, RegisterView,
                              VerifyCodeView)

app_name = UsersConfig.name

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="/"), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-code/", VerifyCodeView.as_view(), name="verify-code"),
    path("account/", AccountView.as_view(), name="account"),
]
