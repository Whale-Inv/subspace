from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from apps.users.models import User
from apps.users.serializers import UserSerializer


class UserCreateAPIView(CreateAPIView):
    """
        Создание пользователя
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = (AllowAny,)