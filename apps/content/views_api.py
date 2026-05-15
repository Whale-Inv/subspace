from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.payments.services import get_subscription_status

from .models import Content
from .permissions import IsAuthorOrReadOnly
from .serializers import ContentSerializer


class ContentListAPIView(generics.ListAPIView):
    """
    Просмотр списка контента
    """

    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [permissions.AllowAny]


class ContentCreateView(generics.CreateAPIView):
    """
    Создание нового контента
    """

    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


@swagger_auto_schema(security=[{"Bearer": []}])
class ContentRetrieveView(generics.RetrieveAPIView):
    """
    Просмотр одного контента
    """

    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Если контент платный
        if instance.is_paid:
            # Проверяем авторизацию
            if not request.user.is_authenticated:
                return Response(
                    {"error": "Требуется авторизация"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Проверяем подписку
            if not get_subscription_status(request.user):
                return Response(
                    {"error": "Требуется подписка для доступа"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ContentUpdateView(generics.UpdateAPIView):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]


class ContentDestroyView(generics.DestroyAPIView):
    queryset = Content.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
