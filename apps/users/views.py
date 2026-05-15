import random

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from apps.payments.services import has_active_subscription
from apps.users.forms import LoginForm, UserRegistrationForm

User = get_user_model()


def generate_code():
    return str(random.randint(1000, 9999))


class LoginView(FormView):
    template_name = "users/login.html"
    form_class = LoginForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        phone_number = form.cleaned_data["phone_number"]
        password = form.cleaned_data["password"]

        user = authenticate(self.request, username=phone_number, password=password)

        if user:
            login(self.request, user)
            return super().form_valid(form)

        form.add_error(None, "Неверный номер телефона или пароль")
        return self.form_invalid(form)


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect("/")


class RegisterView(FormView):
    form_class = UserRegistrationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:verify-code")

    def form_valid(self, form):
        # Сохраняем данные регистрации в сессию
        self.request.session["register_data"] = form.cleaned_data

        # Генерируем и сохраняем код в сессию
        code = generate_code()
        self.request.session["verification_code"] = code

        # Печатаем код в консоль
        print(
            f"Код подтверждения для {form.cleaned_data['phone_number']}: {code}",
            flush=True,
        )
        return super().form_valid(form)


class AccountView(LoginRequiredMixin, TemplateView):
    template_name = "users/account.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Проверяем наличие подписки
        if hasattr(user, "subscription") and user.subscription:
            context["has_access"] = has_active_subscription(user)
            context["end_date"] = user.subscription.end_date
            context["subscription"] = user.subscription
            context["subscription_exists"] = True
        else:
            context["has_access"] = False
            context["subscription_exists"] = False
            context["subscription"] = None

        return context


class VerifyCodeView(TemplateView):
    template_name = "users/verify_code.html"

    def post(self, request):
        entered_code = request.POST.get("code")
        saved_code = request.session.get("verification_code")
        register_data = request.session.get("register_data")

        if not register_data:
            return redirect("users:register")

        if saved_code and entered_code == saved_code:
            # Код верный — создаём пользователя
            user = User.objects.create_user(
                phone_number=register_data["phone_number"],
                first_name=register_data["first_name"],
                email=register_data.get("email", ""),
                password=register_data["password"],
            )
            login(request, user)

            # Чистим сессию
            request.session.pop("verification_code", None)
            request.session.pop("register_data", None)

            return redirect("home")
        else:
            return self.render_to_response({"error": "Неверный код подтверждения"})

    def get(self, request):
        if not request.session.get("register_data"):
            return redirect("users:register")
        return self.render_to_response({})
