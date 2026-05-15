from django.contrib.auth import get_user_model
from django.forms import (CharField, EmailInput, Form, ModelForm,
                          PasswordInput, TextInput, forms)


class LoginForm(Form):
    phone_number = CharField(max_length=20, label="Номер телефона")
    password = CharField(widget=PasswordInput, label="Пароль")


User = get_user_model()


class UserRegistrationForm(ModelForm):
    password = CharField(
        label="Пароль", widget=PasswordInput(attrs={"class": "form-control"})
    )
    password2 = CharField(
        label="Подтверждение", widget=PasswordInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = User
        fields = ["phone_number", "first_name", "email"]
        widgets = {
            "phone_number": TextInput(
                attrs={"class": "form-control", "placeholder": "+79001234567"}
            ),
            "first_name": TextInput(
                attrs={"class": "form-control", "placeholder": "Ваше имя"}
            ),
            "email": EmailInput(
                attrs={"class": "form-control", "placeholder": "example@mail.ru"}
            ),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if User.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("Номер уже существует")
        return phone_number

    def clean(self):
        if self.cleaned_data.get("password") != self.cleaned_data.get("password2"):
            raise forms.ValidationError("Пароли не совпадают")
        return self.cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
