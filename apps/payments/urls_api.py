from django.urls import path

from apps.payments.apps import PaymentsConfig
from apps.payments.views_api import (CancelSubscriptionAPIView,
                                     CreateCheckoutSessionView,
                                     SubscriptionStatusView)

app_name = PaymentsConfig.name

urlpatterns = [
    path(
        "create-checkout/", CreateCheckoutSessionView.as_view(), name="create-checkout"
    ),
    path("status/", SubscriptionStatusView.as_view(), name="subscription-status"),
    path(
        "cancel-subscription/",
        CancelSubscriptionAPIView.as_view(),
        name="cancel-subscription",
    ),
]
