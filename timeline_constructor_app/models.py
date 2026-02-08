from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator



class Timeline(models.Model):
    COLOR_SCHEMES = [
        ('green', 'Зеленая'),
        ('blue', 'Синяя'),
        ('purple', 'Фиолетовая'),
        ('orange', 'Оранжевая'),
        ('red', 'Красная'),
        ('teal', 'Бирюзовая'),
    ]

    LAYOUT_CHOICES = [
        ('vertical', 'Вертикальный'),
        ('horizontal', 'Горизонтальный'),
        ('centered', 'Центрированный'),
    ]

    border_color = models.CharField(max_length=20, default='#10b981', verbose_name='Цвет рамки')

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True)
    color_scheme = models.CharField(max_length=20, choices=COLOR_SCHEMES, default='green')
    layout = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='vertical')
    show_dates = models.BooleanField(default=True)
    show_images = models.BooleanField(default=True)
    allow_comments = models.BooleanField(default=True)

    # Новые поля для доски (добавьте эти строки)
    board_x = models.FloatField(default=0, verbose_name='Позиция X на доске')
    board_y = models.FloatField(default=0, verbose_name='Позиция Y на доске')

    # Связи для иерархии на доске
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительский таймлайн'
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('timeline_detail', kwargs={'pk': self.pk})

    def events_count(self):
        return self.events.count()


class TimelineEvent(models.Model):
    ERA_CHOICES = [
        ('ancient', '🏛️ Древняя математика (до 500 г.)'),
        ('medieval', '⛪ Средневековая математика (500-1500)'),
        ('renaissance', '🎨 Эпоха Возрождения (1500-1700)'),
        ('enlightenment', '💡 Эпоха Просвещения (1700-1800)'),
        ('modern', '🔬 Современная математика (1800-1950)'),
        ('contemporary', '💻 Современность (1950-настоящее время)'),
    ]

    EVENT_TYPES = [
        ('discovery', '🔍 Открытие'),
        ('invention', '⚡ Изобретение'),
        ('publication', '📚 Публикация'),
        ('theory', '🧠 Теория'),
        ('method', '🛠️ Метод'),
        ('award', '🏆 Награда'),
        ('birth', '👶 Рождение'),
        ('death', '⚰️ Смерть'),
        ('event', '📅 Событие'),
    ]

    timeline = models.ForeignKey(Timeline, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    detailed_description = models.TextField(blank=True)
    year = models.IntegerField(validators=[MinValueValidator(-3000), MaxValueValidator(2100)])
    month = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    day = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(31)])
    era = models.CharField(max_length=20, choices=ERA_CHOICES)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='event')
    importance = models.IntegerField(default=2, choices=[(1, '⭐ Низкая'), (2, '⭐⭐ Средняя'), (3, '⭐⭐⭐ Высокая')])
    image = models.ImageField(upload_to='timeline_images/', blank=True, null=True)
    source_link = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.year})"

    @property
    def tags_str(self) -> str:
        return str(self.tags)

    def get_tags_list(self) -> list[str]:
        if self.tags:
            return [tag.strip() for tag in self.tags_str.split(',')]
        return []

    board_x = models.FloatField(default=0, verbose_name='Позиция X на доске')
    board_y = models.FloatField(default=0, verbose_name='Позиция Y на доске')


class TimelineComment(models.Model):
    timeline = models.ForeignKey(Timeline, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.username}: {self.text[:50]}"


class TimelineLike(models.Model):
    timeline = models.ForeignKey(Timeline, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['timeline', 'user']


class TimelineView(models.Model):
    timeline = models.ForeignKey(Timeline, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    viewed_at = models.DateTimeField(auto_now_add=True)


class BoardConnection(models.Model):
    source = models.ForeignKey(
        Timeline,
        on_delete=models.CASCADE,
        related_name='outgoing_connections'
    )
    target = models.ForeignKey(
        Timeline,
        on_delete=models.CASCADE,
        related_name='incoming_connections'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['source', 'target']

    def __str__(self):
        return f"{self.source} → {self.target}"


class BoardTimeline(models.Model):
    """Отдельная модель для таймлайнов на доске"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Связь с основным таймлайном (опционально)
    original_timeline = models.ForeignKey(
        'timeline_constructor_app.Timeline',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timeline_board_versions'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='timeline_board_timelines'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Позиция на доске
    x = models.FloatField(default=0)
    y = models.FloatField(default=0)
    width = models.IntegerField(default=280)  # Ширина узла
    height = models.IntegerField(default=180)  # Высота узла

    # Визуальные настройки (только для доски)
    color = models.CharField(max_length=20, default='#10b981')
    z_index = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class BoardNode(models.Model):
    """Узел на доске"""
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")

    # Позиция на доске
    x = models.FloatField(default=100, verbose_name="Позиция X")
    y = models.FloatField(default=100, verbose_name="Позиция Y")

    # Цвета
    color = models.CharField(max_length=20, default='#10b981', verbose_name="Цвет заголовка")
    bg_color = models.CharField(max_length=20, default='#ffffff', verbose_name="Цвет фона")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Узел доски"
        verbose_name_plural = "Узлы доски"

    def __str__(self):
        return self.title