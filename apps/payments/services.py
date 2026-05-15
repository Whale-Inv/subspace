import time
from datetime import timedelta

import stripe
from django.conf import settings
from django.utils import timezone

from .models import Subscription

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_checkout(user, success_url, cancel_url):
    """
    Создает Stripe Checkout Session для подписки
    """

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "rub",
                    "product_data": {
                        "name": "SubSpace Premium",
                        "description": "Доступ ко всем платным материалам",
                    },
                    "unit_amount": 49900,  # 499.00 рублей
                    "recurring": {"interval": "month"},  # Подписка
                },
                "quantity": 1,
            }
        ],
        mode="subscription",  # Режим подписки
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
        client_reference_id=str(user.id),
        metadata={
            "user_id": user.id,
        },
    )

    return session


def get_subscription_status(user):
    """
    Проверяет активна ли подписка у пользователя
    """
    return has_active_subscription(user)


def create_subscription_from_webhook(
    user_id, stripe_subscription_id, stripe_customer_id
):
    """
    Создает подписку в БД после успешной оплаты
    """

    subscription, created = Subscription.objects.update_or_create(
        user_id=user_id,
        defaults={
            "stripe_subscription_id": stripe_subscription_id,
            "stripe_customer_id": stripe_customer_id,
            "is_active": True,
            "end_date": timezone.now() + timedelta(days=30),
            "is_cancelled": False,
        },
    )
    return subscription


def cancel_subscription(user):
    if user.subscription and user.subscription.stripe_subscription_id:
        stripe.Subscription.modify(
            user.subscription.stripe_subscription_id, cancel_at_period_end=True
        )
        user.subscription.is_cancelled = True
        user.subscription.save()


def activate_subscription_from_session(session_id, retry=True):
    """
    Активирует подписку из session_id (для локального тестирования без вебхука)
    """
    session = stripe.checkout.Session.retrieve(session_id)

    user_id = session.client_reference_id
    stripe_subscription_id = session.subscription
    stripe_customer_id = session.customer
    payment_status = session.payment_status

    if user_id and stripe_subscription_id and payment_status == "paid":
        create_subscription_from_webhook(
            user_id, stripe_subscription_id, stripe_customer_id
        )
        pass
    elif retry:
        time.sleep(5)
        return activate_subscription_from_session(session_id, retry=False)

    return None


def has_active_subscription(user):
    """
    Есть ли доступ к платному контенту
    """
    if hasattr(user, "subscription") and user.subscription.end_date:
        return user.subscription.end_date > timezone.now()
    return False


def is_subscription_cancellable(user):
    """
    Можно ли отменить подписку (есть активная И не отменена еще)
    """
    if hasattr(user, "subscription") and user.subscription:
        return (
            user.subscription.end_date
            and user.subscription.end_date > timezone.now()
            and not user.subscription.is_cancelled
        )
    return False
