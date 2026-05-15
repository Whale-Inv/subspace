from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Subscription
from .services import (activate_subscription_from_session, cancel_subscription,
                       create_stripe_checkout,
                       create_subscription_from_webhook,
                       has_active_subscription)

User = get_user_model()


class SubscriptionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone_number="+79001234567")

    def test_create_subscription(self):
        sub = Subscription.objects.create(
            user=self.user,
            stripe_subscription_id="sub_test_123",
            stripe_customer_id="cus_test_123",
            is_active=True,
        )
        self.assertEqual(sub.user.phone_number, "+79001234567")
        self.assertTrue(sub.is_active)

    def test_subscription_str(self):
        sub = Subscription.objects.create(user=self.user)
        self.assertIn(self.user.phone_number, str(sub))


class CreateStripeCheckoutTest(TestCase):
    """
    Тесты для функции create_stripe_checkout
    """

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+79001234567", password="testpass123"
        )
        self.success_url = "https://example.com/success"
        self.cancel_url = "https://example.com/cancel"

    @patch("stripe.checkout.Session.create")
    def test_create_stripe_checkout_calls_stripe_with_correct_params(
        self, mock_stripe_create
    ):
        """
        Проверка, что Stripe вызван с правильными параметрами
        """
        # Мокаем ответ Stripe
        mock_session = MagicMock()
        mock_session.id = "cs_test_123"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe_create.return_value = mock_session

        create_stripe_checkout(self.user, self.success_url, self.cancel_url)

        # Проверяем, что Stripe был вызван один раз
        mock_stripe_create.assert_called_once()

        # Проверяем параметры вызова
        call_kwargs = mock_stripe_create.call_args[1]
        self.assertEqual(call_kwargs["mode"], "subscription")
        self.assertEqual(call_kwargs["payment_method_types"], ["card"])
        self.assertEqual(
            call_kwargs["success_url"],
            self.success_url + "?session_id={CHECKOUT_SESSION_ID}",
        )
        self.assertEqual(call_kwargs["cancel_url"], self.cancel_url)
        self.assertEqual(call_kwargs["client_reference_id"], str(self.user.id))
        self.assertEqual(call_kwargs["metadata"]["user_id"], self.user.id)

    @patch("stripe.checkout.Session.create")
    def test_create_stripe_checkout_returns_session(self, mock_stripe_create):
        """
        Проверка, что функция возвращает объект сессии
        """
        mock_session = MagicMock()
        mock_session.id = "cs_test_456"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe_create.return_value = mock_session

        result = create_stripe_checkout(self.user, self.success_url, self.cancel_url)

        self.assertEqual(result, mock_session)
        self.assertEqual(result.id, "cs_test_456")

    @patch("stripe.checkout.Session.create")
    def test_create_stripe_checkout_line_items_structure(self, mock_stripe_create):
        """
        Проверка структуры line_items
        """
        mock_session = MagicMock()
        mock_stripe_create.return_value = mock_session

        create_stripe_checkout(self.user, self.success_url, self.cancel_url)

        call_kwargs = mock_stripe_create.call_args[1]
        line_items = call_kwargs["line_items"]

        self.assertEqual(len(line_items), 1)
        self.assertEqual(line_items[0]["quantity"], 1)
        self.assertEqual(line_items[0]["price_data"]["currency"], "rub")
        self.assertEqual(line_items[0]["price_data"]["unit_amount"], 49900)
        self.assertEqual(
            line_items[0]["price_data"]["product_data"]["name"], "SubSpace Premium"
        )
        self.assertEqual(line_items[0]["price_data"]["recurring"]["interval"], "month")

    @patch("stripe.checkout.Session.create")
    def test_create_stripe_checkout_handles_stripe_exception(self, mock_stripe_create):
        """
        Проверка обработки исключений Stripe
        """
        mock_stripe_create.side_effect = Exception("Stripe API error")

        with self.assertRaises(Exception) as context:
            create_stripe_checkout(self.user, self.success_url, self.cancel_url)

        self.assertIn("Stripe API error", str(context.exception))


class CreateSubscriptionFromWebhookTest(TestCase):
    """
    Тесты для функции create_subscription_from_webhook
    """

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+79001234567", password="testpass123"
        )
        self.user_id = self.user.id
        self.stripe_subscription_id = "sub_test_123"
        self.stripe_customer_id = "cus_test_456"

    def test_create_new_subscription_when_not_exists(self):
        """
        Создание новой подписки, если её нет
        """
        self.assertEqual(Subscription.objects.count(), 0)

        subscription = create_subscription_from_webhook(
            user_id=self.user_id,
            stripe_subscription_id=self.stripe_subscription_id,
            stripe_customer_id=self.stripe_customer_id,
        )

        # Проверяем, что подписка создалась
        self.assertEqual(Subscription.objects.count(), 1)
        self.assertEqual(subscription.user_id, self.user_id)
        self.assertEqual(
            subscription.stripe_subscription_id, self.stripe_subscription_id
        )
        self.assertEqual(subscription.stripe_customer_id, self.stripe_customer_id)
        self.assertTrue(subscription.is_active)
        self.assertFalse(subscription.is_cancelled)

        # Проверяем end_date (должен быть через ~30 дней)
        expected_end = timezone.now() + timedelta(days=30)
        # Допускаем погрешность в 5 секунд
        diff = abs((subscription.end_date - expected_end).total_seconds())
        self.assertLess(diff, 5)

    def test_update_existing_subscription(self):
        """
        Обновление существующей подписки
        """
        # Сначала создаём подписку
        old_subscription = Subscription.objects.create(
            user=self.user,
            stripe_subscription_id="old_id",
            stripe_customer_id="old_cus",
            is_active=False,
            end_date=timezone.now() - timedelta(days=1),
        )

        # Обновляем через вебхук
        subscription = create_subscription_from_webhook(
            user_id=self.user_id,
            stripe_subscription_id=self.stripe_subscription_id,
            stripe_customer_id=self.stripe_customer_id,
        )

        # Проверяем, что подписка обновилась (не создалась новая)
        self.assertEqual(Subscription.objects.count(), 1)
        self.assertEqual(subscription.id, old_subscription.id)
        self.assertEqual(
            subscription.stripe_subscription_id, self.stripe_subscription_id
        )
        self.assertEqual(subscription.stripe_customer_id, self.stripe_customer_id)
        self.assertTrue(subscription.is_active)

    def test_subscription_activation_sets_correct_fields(self):
        """
        Проверка, что активированная подписка имеет правильные поля
        """
        subscription = create_subscription_from_webhook(
            user_id=self.user_id,
            stripe_subscription_id=self.stripe_subscription_id,
            stripe_customer_id=self.stripe_customer_id,
        )

        self.assertTrue(subscription.is_active)
        self.assertFalse(subscription.is_cancelled)
        self.assertIsNotNone(subscription.end_date)
        self.assertGreater(subscription.end_date, timezone.now())

    def test_returns_subscription_object(self):
        """
        Проверка, что функция возвращает объект подписки
        """
        subscription = create_subscription_from_webhook(
            user_id=self.user_id,
            stripe_subscription_id=self.stripe_subscription_id,
            stripe_customer_id=self.stripe_customer_id,
        )

        self.assertIsInstance(subscription, Subscription)
        self.assertEqual(subscription.user_id, self.user_id)


class CancelSubscriptionTest(TestCase):
    """
    Тесты для функции cancel_subscription
    """

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+79001234567", password="testpass123"
        )

    @patch("stripe.Subscription.modify")
    def test_cancel_subscription_with_valid_subscription(self, mock_stripe_modify):
        """
        Отмена существующей подписки
        """
        subscription = Subscription.objects.create(
            user=self.user,
            stripe_subscription_id="sub_test_123",
            is_active=True,
            is_cancelled=False,
            end_date=timezone.now() + timedelta(days=30),
        )

        cancel_subscription(self.user)

        # Проверяем вызов Stripe
        mock_stripe_modify.assert_called_once_with(
            "sub_test_123", cancel_at_period_end=True
        )

        # Проверяем обновление БД
        subscription.refresh_from_db()
        self.assertTrue(subscription.is_cancelled)


class ActivateSubscriptionFromSessionTest(TestCase):
    """
    Тесты для функции activate_subscription_from_session
    """

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+79001234567", password="testpass123"
        )
        self.session_id = "cs_test_123"

    @patch("stripe.checkout.Session.retrieve")
    @patch("apps.payments.services.create_subscription_from_webhook")
    def test_activate_with_paid_subscription(
        self, mock_create_subscription, mock_stripe_retrieve
    ):
        """
        Успешная активация: payment_status = 'paid'
        """
        mock_session = MagicMock()
        mock_session.client_reference_id = str(self.user.id)
        mock_session.subscription = "sub_test_123"
        mock_session.customer = "cus_test_456"
        mock_session.payment_status = "paid"
        mock_stripe_retrieve.return_value = mock_session

        result = activate_subscription_from_session(self.session_id, retry=False)

        mock_create_subscription.assert_called_once_with(
            str(self.user.id), "sub_test_123", "cus_test_456"
        )
        self.assertIsNone(result)

    @patch("stripe.checkout.Session.retrieve")
    @patch("apps.payments.services.create_subscription_from_webhook")
    def test_activate_with_unpaid_subscription_no_retry(
        self, mock_create_subscription, mock_stripe_retrieve
    ):
        """
        Неуспешная активация: payment_status != 'paid', retry=False
        """
        mock_session = MagicMock()
        mock_session.client_reference_id = str(self.user.id)
        mock_session.subscription = "sub_test_123"
        mock_session.payment_status = "unpaid"
        mock_stripe_retrieve.return_value = mock_session

        result = activate_subscription_from_session(self.session_id, retry=False)

        mock_create_subscription.assert_not_called()
        self.assertIsNone(result)

    @patch("stripe.checkout.Session.retrieve")
    @patch("time.sleep", return_value=None)
    @patch("apps.payments.services.create_subscription_from_webhook")
    def test_activate_with_retry(
        self, mock_create_subscription, mock_sleep, mock_stripe_retrieve
    ):
        """
        Проверка повторной попытки при retry=True
        """
        # Первый вызов — unpaid
        mock_session_unpaid = MagicMock()
        mock_session_unpaid.payment_status = "unpaid"
        mock_session_unpaid.client_reference_id = str(self.user.id)
        mock_session_unpaid.subscription = "sub_test_123"

        # Второй вызов — paid
        mock_session_paid = MagicMock()
        mock_session_paid.payment_status = "paid"
        mock_session_paid.client_reference_id = str(self.user.id)
        mock_session_paid.subscription = "sub_test_123"
        mock_session_paid.customer = "cus_test_456"

        mock_stripe_retrieve.side_effect = [mock_session_unpaid, mock_session_paid]

        with patch(
            "apps.payments.services.activate_subscription_from_session",
            wraps=activate_subscription_from_session,
        ):
            # Запускаем с retry=True
            activate_subscription_from_session(self.session_id, retry=True)

            # Должна быть создана подписка
            mock_create_subscription.assert_called_once()

    @patch("stripe.checkout.Session.retrieve")
    def test_activate_missing_user_id(self, mock_stripe_retrieve):
        """
        Нет user_id в сессии
        """
        mock_session = MagicMock()
        mock_session.client_reference_id = None
        mock_session.subscription = "sub_test_123"
        mock_session.payment_status = "paid"
        mock_stripe_retrieve.return_value = mock_session

        result = activate_subscription_from_session(self.session_id, retry=False)

        self.assertIsNone(result)

    @patch("stripe.checkout.Session.retrieve")
    def test_activate_missing_subscription_id(self, mock_stripe_retrieve):
        """
        Нет subscription в сессии
        """
        mock_session = MagicMock()
        mock_session.client_reference_id = str(self.user.id)
        mock_session.subscription = None
        mock_session.payment_status = "paid"
        mock_stripe_retrieve.return_value = mock_session

        result = activate_subscription_from_session(self.session_id, retry=False)

        self.assertIsNone(result)


class HasActiveSubscriptionTest(TestCase):
    """
    Тесты для функции has_active_subscription
    """

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+79001234567", password="testpass123"
        )

    def test_has_active_subscription_true(self):
        """
        Активная подписка с end_date в будущем
        """
        Subscription.objects.create(
            user=self.user, end_date=timezone.now() + timedelta(days=30)
        )
        self.assertTrue(has_active_subscription(self.user))

    def test_has_active_subscription_false_expired(self):
        """
        Истекшая подписка
        """
        Subscription.objects.create(
            user=self.user, end_date=timezone.now() - timedelta(days=1)
        )
        self.assertFalse(has_active_subscription(self.user))

    def test_has_active_subscription_false_no_subscription(self):
        """
        Нет подписки у пользователя
        """
        self.assertFalse(has_active_subscription(self.user))

    def test_has_active_subscription_false_no_end_date(self):
        """
        Подписка без end_date
        """
        Subscription.objects.create(user=self.user, end_date=None)
        self.assertFalse(has_active_subscription(self.user))

    def test_has_active_subscription_with_cancelled_but_not_expired(self):
        """
        Отменённая подписка, но end_date ещё в будущем — доступ есть
        """
        Subscription.objects.create(
            user=self.user,
            end_date=timezone.now() + timedelta(days=30),
            is_cancelled=True,
        )
        self.assertTrue(has_active_subscription(self.user))


class CancelSubscriptionViewTest(TestCase):
    """
    Тесты для CancelSubscriptionView
    """

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+79001234567", password="testpass123"
        )
        self.url = reverse("payments:cancel-subscription")
        self.account_url = reverse("users:account")

    def test_redirects_to_login_for_unauthenticated(self):
        """
        Неавторизованный пользователь редиректится на логин
        """
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response.url)

    @patch("apps.payments.views.cancel_subscription")
    def test_cancel_subscription_when_user_has_subscription(self, mock_cancel):
        """
        Пользователь с подпиской — отмена успешна
        """
        Subscription.objects.create(
            user=self.user,
            stripe_subscription_id="sub_test_123",
            is_active=True,
            is_cancelled=False,
        )

        self.client.force_login(self.user)
        response = self.client.post(self.url, follow=True)

        mock_cancel.assert_called_once_with(self.user)
        self.assertRedirects(response, self.account_url)

        # Проверяем сообщение об успехе
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("отменена" in str(m) for m in messages))

    @patch("apps.payments.views.cancel_subscription")
    def test_cancel_subscription_when_user_has_no_subscription(self, mock_cancel):
        """
        Пользователь без подписки — сообщение об ошибке
        """
        self.client.force_login(self.user)
        response = self.client.post(self.url, follow=True)

        mock_cancel.assert_not_called()
        self.assertRedirects(response, self.account_url)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Нет активной подписки" in str(m) for m in messages))

    @patch("apps.payments.views.cancel_subscription")
    def test_cancel_subscription_with_subscription_but_no_stripe_id(self, mock_cancel):
        """
        Пользователь с подпиской, но без stripe_id
        """
        Subscription.objects.create(
            user=self.user,
            stripe_subscription_id="",
            is_active=True,
            is_cancelled=False,
        )

        self.client.force_login(self.user)
        response = self.client.post(self.url, follow=True)

        mock_cancel.assert_called_once_with(self.user)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("отменена" in str(m) for m in messages))

    @patch("apps.payments.views.cancel_subscription")
    def test_cancel_subscription_calls_refresh_from_db(self, mock_cancel):
        """
        Проверка, что refresh_from_db вызывается после отмены
        """
        Subscription.objects.create(
            user=self.user,
            stripe_subscription_id="sub_test_123",
            is_active=True,
            is_cancelled=False,
        )

        self.client.force_login(self.user)

        # Мокаем refresh_from_db на самом пользователе
        with patch.object(User, "refresh_from_db") as mock_refresh:
            self.client.post(self.url)
            mock_refresh.assert_called_once()
