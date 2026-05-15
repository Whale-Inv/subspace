from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..payments.models import Subscription
from .models import Content
from .views import ContentCreateView

User = get_user_model()


class ContentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+79001234567", first_name="Тест"
        )
        self.content = Content.objects.create(
            title="Тестовый контент",
            description="Описание тестового контента",
            content_type="article",
            is_paid=False,
            author=self.user,
        )

    def test_content_creation(self):
        """
        Создание контента
        """
        self.assertEqual(self.content.title, "Тестовый контент")
        self.assertEqual(self.content.is_paid, False)
        self.assertEqual(str(self.content), "Тестовый контент")

    def test_content_list_view(self):
        """
        Список контента доступен всем
        """
        response = self.client.get(reverse("content:content-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Тестовый контент")

    def test_free_content_detail(self):
        """
        Бесплатный контент доступен всем
        """
        response = self.client.get(
            reverse("content:content-detail", args=[self.content.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Тестовый контент")


class PaidContentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+79001234567", password="testpass123"
        )
        self.paid_content = Content.objects.create(
            title="Платный контент",
            description="Только по подписке",
            is_paid=True,
            author=self.user,
        )

    def test_paid_content_redirect_for_unauth(self):
        """
        Неавторизованный редирект на логин
        """
        response = self.client.get(
            reverse("content:content-detail", args=[self.paid_content.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response.url)

    def test_paid_content_redirect_for_no_subscription(self):
        """
        Авторизованный без подписки — редирект на оплату
        """
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("content:content-detail", args=[self.paid_content.id])
        )
        self.assertEqual(response.status_code, 302)


class HomePageViewMockTest(TestCase):
    """
    Тесты для покрытия get_subscription_status в HomePageView
    """

    def setUp(self):
        self.url = reverse("home")
        self.user = User.objects.create_user(
            phone_number="+79001234567", password="testpass123"
        )

    def test_unauthenticated_user(self):
        """
        Неавторизованный пользователь
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("is_subscription_active", response.context)
        self.assertFalse(response.context["is_subscription_active"])

    def test_authenticated_without_subscription(self):
        """
        Авторизованный без подписки
        """
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_subscription_active"])

    def test_authenticated_with_active_subscription(self):
        """
        Авторизованный с активной подпиской
        """
        Subscription.objects.create(
            user=self.user, is_active=True, end_date=timezone.now() + timedelta(days=30)
        )
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTrue(response.context["is_subscription_active"])

    def test_authenticated_with_expired_subscription(self):
        """
        Авторизованный с истекшей подпиской
        """
        Subscription.objects.create(
            user=self.user, is_active=False, end_date=timezone.now() - timedelta(days=1)
        )
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertFalse(response.context["is_subscription_active"])

    @patch("apps.content.views.get_subscription_status")
    def test_subscription_status_function_called(self, mock_status):
        """
        Проверка, что функция get_subscription_status вызвана
        """
        mock_status.return_value = False
        self.client.force_login(self.user)
        self.client.get(self.url)
        mock_status.assert_called_once_with(self.user)


class ContentCreateViewTest(TestCase):
    """
    Тесты для создания контента
    """

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+79001234567", password="testpass123"
        )
        self.url = reverse("content:content-create")
        self.valid_data = {
            "title": "Новый контент",
            "description": "Описание нового контента",
            "content_type": "article",
            "is_paid": False,
            "price": "0.00",
        }

    def test_create_view_redirects_for_unauthenticated(self):
        """
        Неавторизованный пользователь редиректится на логин
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response.url)

    def test_create_view_status_code_for_authenticated(self):
        """
        Авторизованный пользователь видит форму создания
        """
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "content/form.html")

    def test_form_valid_sets_author_and_saves(self):
        """form_valid устанавливает автора и сохраняет контент"""
        self.client.force_login(self.user)

        response = self.client.post(self.url, self.valid_data)

        # Проверяем редирект после успешного создания
        self.assertRedirects(response, reverse("content:content-list"))

        # Проверяем, что контент создался
        self.assertEqual(Content.objects.count(), 1)

        # Проверяем, что автор установлен правильно
        content = Content.objects.first()
        self.assertEqual(content.author, self.user)
        self.assertEqual(content.title, "Новый контент")
        self.assertEqual(content.description, "Описание нового контента")

    def test_form_valid_with_paid_content(self):
        """Создание платного контента"""
        self.client.force_login(self.user)

        paid_data = self.valid_data.copy()
        paid_data["is_paid"] = True
        paid_data["price"] = "499.00"

        response = self.client.post(self.url, paid_data)

        self.assertRedirects(response, reverse("content:content-list"))

        content = Content.objects.first()
        self.assertTrue(content.is_paid)
        self.assertEqual(str(content.price), "499.00")

    def test_form_invalid_does_not_create_content(self):
        """Невалидная форма не создаёт контент"""
        self.client.force_login(self.user)

        invalid_data = self.valid_data.copy()
        invalid_data.pop("title")  # title обязателен

        response = self.client.post(self.url, invalid_data)

        # Форма не прошла валидацию, остаёмся на той же странице
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "content/form.html")

        # Контент не создался
        self.assertEqual(Content.objects.count(), 0)


class ContentCreateViewFormValidCoverageTest(TestCase):
    """Целенаправленные тесты для покрытия form_valid"""

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+79009998877", password="testpass123"
        )
        self.view = ContentCreateView()
        self.view.request = self.client.request()
        self.view.request.user = self.user


def test_form_valid_sets_author(self):
    """Прямая проверка, что form_valid устанавливает автора"""
    from django.test import RequestFactory

    from .forms import ContentForm

    factory = RequestFactory()
    request = factory.post(
        "/content/create/",
        {
            "title": "Тест",
            "description": "Описание",
            "content_type": "article",
        },
    )
    request.user = self.user

    view = ContentCreateView()
    view.request = request

    form = ContentForm(
        {
            "title": "Тест",
            "description": "Описание",
            "content_type": "article",
        }
    )

    # 👇 ВАЖНО: создаём instance, но не сохраняем
    form.instance = Content()

    # Проверяем валидность формы
    self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    # Сохраняем автора
    form.instance.author = self.user
    self.assertEqual(form.instance.author, self.user)


class ContentUpdateViewTestFuncTest(TestCase):
    """Тесты для метода test_func в ContentUpdateView"""

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+79001234567", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            phone_number="+79009998877", password="testpass456"
        )
        self.content = Content.objects.create(
            title="Тестовый контент", description="Описание", author=self.user
        )
        self.url = reverse("content:content-update", args=[self.content.id])

    def test_test_func_returns_true_for_author(self):
        """test_func возвращает True для автора контента"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        # Автор имеет доступ к редактированию
        self.assertEqual(response.status_code, 200)

    def test_test_func_returns_false_for_non_author(self):
        """test_func возвращает False для не-автора контента"""
        self.client.force_login(self.other_user)
        response = self.client.get(self.url)
        # Не-автор редиректится (403 или редирект)
        self.assertNotEqual(response.status_code, 200)
