from rest_framework import serializers

from apps.content.models import Content


class ContentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.first_name', read_only=True)

    class Meta:
        model = Content
        fields = "__all__"
        read_only_fields = ['author', 'created_at', 'updated_at']

