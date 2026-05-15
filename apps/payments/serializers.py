from rest_framework import serializers

from .models import Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source="user.phone_number", read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "user",
            "user_phone",
            "is_active",
            "start_date",
            "end_date",
            "created_at",
        ]
        read_only_fields = ["user", "user_phone", "start_date", "created_at"]
