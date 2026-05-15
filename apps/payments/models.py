from django.conf import settings
from django.db import models


class Subscription(models.Model):
    """
    Модель подписки пользователя
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
        verbose_name="Пользователь",
    )

    stripe_subscription_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="ID подписки в Stripe"
    )

    stripe_customer_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="ID клиента в Stripe"
    )

    is_active = models.BooleanField(default=False, verbose_name="Активна")

    start_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата начала")

    end_date = models.DateTimeField(
        blank=True, null=True, verbose_name="Дата окончания"
    )
    is_cancelled = models.BooleanField(default=False, verbose_name="Отменена")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.phone_number} - {'Активна' if self.is_active else 'Не активна'}"

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
