from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import Content

User = get_user_model()


class ContentAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone_number="+79001234567", password="testpass123"
        )
        self.content = Content.objects.create(
            title="API Test Content",
            description="Test description",
            is_paid=False,
            author=self.user,
        )

    def test_content_list_api(self):
        """
        GET /api/content/ - список контента
        """
        url = reverse("content-api:content-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_content_detail_api(self):
        """
        GET /api/content/1/ - детали контента
        """
        url = reverse("content-api:content-detail", args=[self.content.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "API Test Content")

    def test_content_create_api_unauth(self):
        """
        POST /api/content/ - без авторизации
        """
        url = reverse("content-api:content-create")
        data = {
            "title": "New Content",
            "description": "New description",
            "is_paid": False,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_content_create_api_auth(self):
        """
        POST /api/content/ - с авторизацией
        """
        self.client.force_authenticate(user=self.user)
        url = reverse("content-api:content-create")
        data = {
            "title": "New Content",
            "description": "New description",
            "is_paid": False,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Content.objects.count(), 2)


class PaidContentAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone_number="+79009998877", password="testpass123"
        )
        self.paid_content = Content.objects.create(
            title="Paid Content",
            description="Need subscription",
            is_paid=True,
            author=self.user,
        )

    def test_paid_content_api_unauth(self):
        """
        Платный контент без авторизации
        """
        url = reverse("content-api:content-detail", args=[self.paid_content.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_paid_content_api_auth_no_subscription(self):
        """
        Платный контент с авторизацией, но без подписки
        """
        self.client.force_authenticate(user=self.user)
        url = reverse("content-api:content-detail", args=[self.paid_content.id])
        response = self.client.get(url)
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_402_PAYMENT_REQUIRED],
        )
