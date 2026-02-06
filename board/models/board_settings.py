from django.db import models
from django.contrib.auth.models import User


class BoardSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")

    # Настройки сетки
    show_grid = models.BooleanField(default=True, verbose_name="Показывать сетку")
    grid_size = models.IntegerField(default=50, verbose_name="Размер сетки")
    grid_color = models.CharField(max_length=20, default='rgba(0,0,0,0.05)', verbose_name="Цвет сетки")

    # Настройки поведения
    snap_to_grid = models.BooleanField(default=True, verbose_name="Привязка к сетке")
    auto_arrange = models.BooleanField(default=False, verbose_name="Авторасположение")

    # Цветовая схема доски
    board_background = models.CharField(max_length=20, default='#f8fafc', verbose_name="Фон доски")

    # Сохраненное состояние
    last_view_x = models.FloatField(default=0, verbose_name="Последняя позиция X")
    last_view_y = models.FloatField(default=0, verbose_name="Последняя позиция Y")
    last_zoom = models.FloatField(default=1, verbose_name="Последний масштаб")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Настройки доски"
        verbose_name_plural = "Настройки досок"

    def __str__(self):
        return f"Настройки доски {self.user.username}"