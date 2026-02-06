from django.db import models
from django.contrib.auth.models import User


class BoardTimeline(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")

    # Связь с основным таймлайном
    original_timeline = models.ForeignKey(
        'timeline_constructor_app.Timeline',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='board_versions',
        verbose_name="Исходный таймлайн"
    )

    # Позиция и размер на доске
    x = models.FloatField(default=100, verbose_name="Позиция X")
    y = models.FloatField(default=100, verbose_name="Позиция Y")
    width = models.IntegerField(default=280, verbose_name="Ширина")
    height = models.IntegerField(default=180, verbose_name="Высота")

    # Визуальные настройки
    color = models.CharField(max_length=20, default='#10b981', verbose_name="Цвет")
    border_color = models.CharField(max_length=20, default='#10b981', verbose_name="Цвет рамки")
    background_color = models.CharField(max_length=20, default='#ffffff', verbose_name="Цвет фона")

    # Состояние
    is_locked = models.BooleanField(default=False, verbose_name="Заблокировано")
    is_collapsed = models.BooleanField(default=False, verbose_name="Свернуто")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Таймлайн на доске"
        verbose_name_plural = "Таймлайны на доске"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.user.username})"