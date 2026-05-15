from django.urls import path

from apps.content.apps import ContentConfig
from apps.content.views import (ContentCreateView, ContentDeleteView,
                                ContentDetailView, ContentListView,
                                ContentUpdateView)

app_name = ContentConfig.name

urlpatterns = [
    path("", ContentListView.as_view(), name="content-list"),
    path("<int:pk>/", ContentDetailView.as_view(), name="content-detail"),
    path("create/", ContentCreateView.as_view(), name="content-create"),
    path("<int:pk>/update/", ContentUpdateView.as_view(), name="content-update"),
    path("<int:pk>/delete/", ContentDeleteView.as_view(), name="content-delete"),
]
