from django.contrib import admin

from .models import Content


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ("title", "content_type", "is_paid", "price", "author", "created_at")
    list_filter = ("is_paid", "content_type")
    search_fields = ("title", "description")
