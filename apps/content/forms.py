from django import forms

from .models import Content


class ContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = [
            "title",
            "description",
            "content_type",
            "is_paid",
            "price",
            "preview",
            "content_file",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 5, "placeholder": "Описание"}
            ),
            "content_type": forms.Select(attrs={"class": "form-select"}),
            "is_paid": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}
            ),
            "preview": forms.FileInput(attrs={"class": "form-control"}),
            "content_file": forms.FileInput(attrs={"class": "form-control"}),
        }
