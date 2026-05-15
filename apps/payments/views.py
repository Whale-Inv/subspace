from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import RedirectView

from .services import (activate_subscription_from_session, cancel_subscription,
                       create_stripe_checkout)


class CreateCheckoutView(LoginRequiredMixin, View):
    """
    Создание сессии оплаты (для браузера)
    """

    def get(self, request):
        user = request.user
        site_url = request.build_absolute_uri("/").rstrip("/")
        success_url = f"{site_url}/payments/success/"
        cancel_url = f"{site_url}/payments/cancel/"

        session = create_stripe_checkout(user, success_url, cancel_url)
        return redirect(session.url)


class CancelSubscriptionView(LoginRequiredMixin, View):
    def post(self, request):

        user = request.user

        if hasattr(user, "subscription"):

            cancel_subscription(user)

            # Обновляем объект из БД
            user.refresh_from_db()
            messages.success(request, "Подписка отменена.")
        else:
            messages.error(request, "Нет активной подписки.")

        return redirect("users:account")


class PaymentSuccessView(RedirectView):
    """Редирект после успешной оплаты"""

    def get(self, request, *args, **kwargs):
        session_id = request.GET.get("session_id")

        if session_id:
            subscription = activate_subscription_from_session(session_id)

            if subscription:
                messages.success(request, "Подписка успешно оформлена!")
            else:
                messages.warning(
                    request, "Подписка оформляется. Статус обновится через минуту."
                )
        else:
            messages.error(request, "Ошибка: session_id не получен.")

        return redirect("home")


class PaymentCancelView(RedirectView):
    """Редирект после отмены оплаты"""

    def get(self, request, *args, **kwargs):
        messages.warning(
            request,
            "Вы отменили оформление подписки. Если передумаете — возвращайтесь!",
        )
        return redirect("home")
