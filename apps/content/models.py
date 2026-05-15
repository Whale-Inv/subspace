from django.conf import settings
from django.db import models


class Content(models.Model):
    """
    Контент (бесплатный или платный)
    """

    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Описание")

    # Тип контента
    TYPE_CHOICES = [
        ("article", "Статья"),
        ("video", "Видео"),
    ]
    content_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default="article"
    )

    # Доступ
    is_paid = models.BooleanField(default=False, verbose_name="Платный")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Цена"
    )

    # Файлы
    preview = models.ImageField(
        upload_to="content/previews/", blank=True, null=True, verbose_name="Превью"
    )

    content_file = models.FileField(
        upload_to="content/files/", blank=True, null=True, verbose_name="Файл контента"
    )

    # Автор
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contents"
    )

    # Даты
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Контент"
        verbose_name_plural = "Контент"
        ordering = ["-created_at"]
