from django.urls import include, path

urlpatterns = [
    path("content/", include("apps.content.urls_api")),
    path("payments/", include("apps.payments.urls_api")),
    path("users/", include("apps.users.urls_api")),
]
