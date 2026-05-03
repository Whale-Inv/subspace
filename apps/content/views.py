from rest_framework import generics, permissions

from .models import Content
from .permissions import IsAuthorOrReadOnly
from .serializers import ContentSerializer


class ContentListView(generics.ListAPIView):
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


class ContentRetrieveView(generics.RetrieveAPIView):
    """
        Просмотр одного контента
    """
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [permissions.AllowAny]


class ContentUpdateView(generics.UpdateAPIView):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]


class ContentDestroyView(generics.DestroyAPIView):
    queryset = Content.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]