from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse

User = get_user_model()


class UserRegistrationTest(TestCase):
    """
    Тесты регистрации с подтверждением по коду
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.register_url = reverse("users:register")
        self.verify_url = reverse("users:verify-code")

    def test_register_form_valid(self):
        """
        Регистрационная форма сохраняет данные в сессию и редиректит
        """
        response = self.client.post(
            self.register_url,
            {
                "phone_number": "+79001234567",
                "first_name": "Тест",
                "email": "test@test.com",
                "password": "testpass123",
                "password2": "testpass123",
            },
        )

        # Проверяем редирект на страницу верификации
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.verify_url)

        # Проверяем, что данные сохранились в сессию
        session = self.client.session
        self.assertIn("register_data", session)
        self.assertIn("verification_code", session)
        self.assertEqual(session["register_data"]["phone_number"], "+79001234567")

    def test_register_form_invalid(self):
        """
        Невалидная форма — ошибка, пользователь не создаётся
        """
        response = self.client.post(
            self.register_url,
            {
                "phone_number": "+79001234567",
                "first_name": "Тест",
                "password": "testpass123",
                "password2": "different",  # Пароли не совпадают
            },
        )

        self.assertEqual(response.status_code, 200)  # Остаёмся на той же странице
        self.assertContains(response, "Пароли не совпадают")

    def test_verify_code_success(self):
        """
        Успешное подтверждение кода — создание пользователя
        """
        # 1. Сначала проходим регистрацию
        self.client.post(
            self.register_url,
            {
                "phone_number": "+79009998877",
                "first_name": "Иван",
                "email": "ivan@test.com",
                "password": "validpass123",
                "password2": "validpass123",
            },
        )

        # Получаем код из сессии
        session = self.client.session
        verification_code = session.get("verification_code")

        # 2. Подтверждаем код
        response = self.client.post(self.verify_url, {"code": verification_code})

        # 3. Проверяем редирект на главную
        self.assertRedirects(response, reverse("home"))

        # 4. Проверяем, что пользователь создался
        user = User.objects.filter(phone_number="+79009998877").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, "Иван")
        self.assertEqual(user.email, "ivan@test.com")

        # 5. Проверяем, что сессия очищена
        session = self.client.session
        self.assertNotIn("register_data", session)
        self.assertNotIn("verification_code", session)

    def test_verify_code_wrong(self):
        """
        Неверный код — пользователь не создаётся
        """
        # 1. Регистрация
        self.client.post(
            self.register_url,
            {
                "phone_number": "+79001112233",
                "first_name": "Петр",
                "password": "pass123",
                "password2": "pass123",
            },
        )

        # 2. Отправляем неверный код
        response = self.client.post(self.verify_url, {"code": "0000"})

        # 3. Должны остаться на странице верификации с ошибкой
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Неверный код подтверждения")

        # 4. Пользователь не должен создаться
        self.assertFalse(User.objects.filter(phone_number="+79001112233").exists())

    def test_verify_code_no_session(self):
        """
        Попытка верификации без сессии регистрации
        """
        response = self.client.get(self.verify_url)
        self.assertRedirects(response, self.register_url)

    def test_verify_code_expired(self):
        """
        Ситуация с истекшим кодом (сессия есть, но проверяем наличие)
        """
        self.client.post(
            self.register_url,
            {
                "phone_number": "+79002223344",
                "first_name": "Анна",
                "password": "pass123",
                "password2": "pass123",
            },
        )

        # Симулируем, что код был утерян/истек (просто чистим)
        session = self.client.session
        session.pop("verification_code", None)
        session.save()

        response = self.client.post(self.verify_url, {"code": "1234"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Неверный код подтверждения")


class UserLoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+79001234567", password="testpass123"
        )
        self.login_url = reverse("users:login")

    def test_login_success(self):
        response = self.client.post(
            self.login_url,
            {
                "phone_number": "+79001234567",
                "password": "testpass123",
            },
        )
        self.assertRedirects(response, reverse("home"))
