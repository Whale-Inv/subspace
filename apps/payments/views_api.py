from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import (activate_subscription_from_session, cancel_subscription,
                       create_stripe_checkout, get_subscription_status)


class CreateCheckoutSessionView(APIView):
    """
    Создание Stripe Checkout
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        # Базовый URL сайта
        site_url = request.build_absolute_uri("/").rstrip("/")
        success_url = f"{site_url}/payments/success/?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{site_url}/payments/cancel/"

        try:
            session = create_stripe_checkout(user, success_url, cancel_url)
            return Response(
                {"checkout_url": session.url, "session_id": session.id},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaymentSuccessView(APIView):
    """
    Обработка успешной оплаты (редирект от Stripe)
    """

    permission_classes = []

    def get(self, request):
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"error": "session_id не указан"}, status=status.HTTP_400_BAD_REQUEST
            )

        subscription = activate_subscription_from_session(session_id)

        if subscription:
            return Response(
                {
                    "message": "Подписка успешно активирована!",
                    "is_active": True,
                    "end_date": subscription.end_date,
                }
            )

        return Response(
            {"error": "Не удалось активировать подписку"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PaymentCancelView(APIView):
    """
    Обработка отмены оплаты
    """

    permission_classes = []

    def get(self, request):
        return Response({"message": "Оплата отменена", "is_active": False})


class SubscriptionStatusView(APIView):
    """
    Проверка статуса подписки текущего пользователя
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        is_active = get_subscription_status(request.user)

        data = {
            "is_active": is_active,
        }

        if hasattr(request.user, "subscription") and request.user.subscription:
            data["end_date"] = request.user.subscription.end_date
            data["start_date"] = request.user.subscription.start_date

        return Response(data)


class CancelSubscriptionAPIView(APIView):
    """
    Отмена подписки
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        if not hasattr(user, "subscription") or not user.subscription.is_active:
            return Response(
                {"error": "У вас нет активной подписки"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cancel_subscription(user)

        return Response(
            {
                "message": "Подписка отменена. Доступ сохранится до конца оплаченного периода.",
                "is_active": False,
                "end_date": user.subscription.end_date,
            }
        )
