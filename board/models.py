from django.db import models
from django.contrib.auth.models import User
from timeline_constructor_app.models import Timeline  # Если нужно связывать


class BoardTimeline(models.Model):
    """Отдельная модель для таймлайнов на доске"""
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")

    # Связь с пользователем
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='board_boardtimelines',
        verbose_name="Пользователь"
    )

    # Связь с основным таймлайном (опционально)
    original_timeline = models.ForeignKey(
        Timeline,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='board_related_timelines',
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

    def get_absolute_url(self):
        return f"/board/#node-{self.id}"

    @property
    def short_description(self):
        """Короткое описание для превью"""
        if len(self.description) > 100:
            return self.description[:100] + "..."
        return self.description


class BoardConnection(models.Model):
    """Соединение между таймлайнами на доске"""
    source = models.ForeignKey(
        BoardTimeline,
        on_delete=models.CASCADE,
        related_name='outgoing_connections',
        verbose_name="Источник"
    )
    target = models.ForeignKey(
        BoardTimeline,
        on_delete=models.CASCADE,
        related_name='incoming_connections',
        verbose_name="Цель"
    )

    label = models.CharField(max_length=100, blank=True, verbose_name="Метка")
    color = models.CharField(max_length=20, default='#3b82f6', verbose_name="Цвет линии")
    line_style = models.CharField(
        max_length=20,
        default='solid',
        choices=[('solid', 'Сплошная'), ('dashed', 'Пунктир'), ('dotted', 'Точки')],
        verbose_name="Стиль линии"
    )
    arrow_type = models.CharField(
        max_length=20,
        default='arrow',
        choices=[('none', 'Без стрелки'), ('arrow', 'Стрелка'), ('circle', 'Круг')],
        verbose_name="Тип стрелки"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Соединение на доске"
        verbose_name_plural = "Соединения на доске"
        unique_together = ['source', 'target']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.source.title} → {self.target.title}"

    def get_line_style(self):
        """Возвращает стиль линии для SVG"""
        styles = {
            'solid': 'none',
            'dashed': '5,5',
            'dotted': '2,2'
        }
        return styles.get(self.line_style, 'none')


class BoardSettings(models.Model):
    """Настройки доски для пользователя"""
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