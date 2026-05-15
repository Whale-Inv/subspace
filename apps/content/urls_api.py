from django.urls import path

from apps.content.views_api import (ContentCreateView, ContentDestroyView,
                                    ContentListAPIView, ContentRetrieveView,
                                    ContentUpdateView)

app_name = "content-api"

urlpatterns = [
    path("", ContentListAPIView.as_view(), name="content-list"),
    path("create/", ContentCreateView.as_view(), name="content-create"),
    path("<int:pk>/", ContentRetrieveView.as_view(), name="content-detail"),
    path("update/<int:pk>/", ContentUpdateView.as_view(), name="content-update"),
    path("delete/<int:pk>/", ContentDestroyView.as_view(), name="content-delete"),
]
