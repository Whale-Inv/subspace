from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "is_active", "start_date", "end_date")
    list_filter = ("is_active",)
    search_fields = ("user__phone_number", "user__email")
    readonly_fields = ("start_date", "created_at", "updated_at")
