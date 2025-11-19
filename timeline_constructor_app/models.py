from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Timeline(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название таймлайна")
    description = models.TextField(verbose_name="Описание", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Создатель")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_public = models.BooleanField(default=True, verbose_name="Публичный доступ")

    # Поле color_scheme удалено

    class Meta:
        verbose_name = "Таймлайн"
        verbose_name_plural = "Таймлайны"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('timeline_detail', kwargs={'pk': self.pk})


class TimelineEvent(models.Model):
    ERA_CHOICES = [
        ('ancient', 'Древняя математика'),
        ('medieval', 'Средневековая математика'),
        ('renaissance', 'Эпоха Возрождения'),
        ('modern', 'Современная математика'),
        ('contemporary', 'Современность'),
    ]

    EVENT_TYPES = [
        ('discovery', 'Открытие'),
        ('invention', 'Изобретение'),
        ('publication', 'Публикация'),
        ('event', 'Событие'),
    ]

    timeline = models.ForeignKey(Timeline, on_delete=models.CASCADE, related_name='events', verbose_name="Таймлайн")
    title = models.CharField(max_length=200, verbose_name="Название события")
    description = models.TextField(verbose_name="Описание события")
    year = models.IntegerField(verbose_name="Год")
    era = models.CharField(max_length=20, choices=ERA_CHOICES, verbose_name="Эпоха")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='event', verbose_name="Тип события")
    importance = models.IntegerField(default=1, choices=[(1, 'Низкая'), (2, 'Средняя'), (3, 'Высокая')],
                                     verbose_name="Важность")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Событие таймлайна"
        verbose_name_plural = "События таймлайна"
        ordering = ['year', 'created_at']

    def __str__(self):
        return f"{self.title} ({self.year})"