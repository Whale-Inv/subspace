from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from apps.content.forms import ContentForm
from apps.content.models import Content
from apps.payments.services import (get_subscription_status,
                                    has_active_subscription)


class HomePageView(ListView):
    model = Content
    template_name = "content/list.html"
    context_object_name = "contents"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_subscription_active"] = get_subscription_status(self.request.user)
        return context


class ContentListView(ListView):
    """
    Список контента
    """

    model = Content
    template_name = "content/list.html"
    context_object_name = "contents"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_subscription_active"] = get_subscription_status(self.request.user)
        return context


class ContentDetailView(DetailView):
    model = Content
    template_name = "content/detail.html"
    context_object_name = "content"

    def get(self, request, *args, **kwargs):
        content = self.get_object()

        # Если контент платный
        if content.is_paid:
            # Проверяем авторизацию
            if not request.user.is_authenticated:
                messages.warning(
                    request, "Для просмотра платного контента нужно авторизоваться."
                )
                return redirect("users:login")

            # Проверяем доступ по подписке
            if not has_active_subscription(request.user):
                messages.warning(
                    request, "Для просмотра этого материала нужна активная подписка."
                )
                return redirect("payments:create-checkout")

        return super().get(request, *args, **kwargs)


class ContentCreateView(LoginRequiredMixin, CreateView):
    model = Content
    form_class = ContentForm
    template_name = "content/form.html"
    success_url = reverse_lazy("content:content-list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class ContentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Content
    form_class = ContentForm
    template_name = "content/form.html"
    success_url = reverse_lazy("content:content-list")

    def test_func(self):
        content = self.get_object()
        return self.request.user == content.author

    def handle_no_permission(self):
        from django.shortcuts import redirect

        return redirect("content:content-list")


class ContentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Content
    template_name = "content/confirm_delete.html"
    success_url = reverse_lazy("content:content-list")

    def test_func(self):
        content = self.get_object()
        return self.request.user == content.author
