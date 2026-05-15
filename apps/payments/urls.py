from django.urls import path

from apps.payments.apps import PaymentsConfig
from apps.payments.views import (CancelSubscriptionView, CreateCheckoutView,
                                 PaymentCancelView, PaymentSuccessView)

app_name = PaymentsConfig.name

urlpatterns = [
    path("create-checkout/", CreateCheckoutView.as_view(), name="create-checkout"),
    path(
        "cancel-subscription/",
        CancelSubscriptionView.as_view(),
        name="cancel-subscription",
    ),
    path("success/", PaymentSuccessView.as_view(), name="success"),
    path("cancel/", PaymentCancelView.as_view(), name="cancel"),
]
