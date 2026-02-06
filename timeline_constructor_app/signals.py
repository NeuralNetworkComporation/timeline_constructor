# signals.py
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Count, Avg
from django.core.cache import cache
from django.utils.text import slugify
import logging

from .models import Timeline, TimelineEvent, TimelineLike, TimelineComment

logger = logging.getLogger(__name__)


# ==================== SIGNAL 1: Автоматический slug для таймлайна ====================
@receiver(pre_save, sender=Timeline)
def auto_generate_timeline_slug(sender, instance, **kwargs):
    """
    Автоматически создает slug для таймлайна из названия.
    Улучшает SEO и читаемость URL.
    """
    if not instance.slug:  # если добавить поле slug в модель
        # Создаем slug из названия (кириллица -> латиница)
        from django.utils.text import slugify
        instance.slug = slugify(instance.title, allow_unicode=False)
        logger.info(f"Создан slug для таймлайна: {instance.slug}")


# ==================== SIGNAL 2: Обновление счетчиков при сохранении события ====================
@receiver(post_save, sender=TimelineEvent)
@receiver(post_delete, sender=TimelineEvent)
def update_timeline_stats(sender, instance, **kwargs):
    """
    Обновляет статистику таймлайна при добавлении/удалении событий.
    Кэширует результаты для быстрого доступа.
    """
    timeline = instance.timeline

    # Обновляем счетчик событий
    event_count = timeline.events.count()

    # Рассчитываем временной диапазон
    events = timeline.events.all()
    if events:
        years = [event.year for event in events]
        timeline.year_start = min(years)
        timeline.year_end = max(years)
    else:
        timeline.year_start = None
        timeline.year_end = None

    # Сохраняем без вызова сигналов (чтобы избежать рекурсии)
    Timeline.objects.filter(pk=timeline.pk).update(
        year_start=timeline.year_start,
        year_end=timeline.year_end
    )

    # Инвалидируем кэш для этого таймлайна
    cache_key = f"timeline_stats_{timeline.pk}"
    cache.delete(cache_key)

    logger.info(f"Обновлена статистика таймлайна #{timeline.pk}")


# ==================== SIGNAL 3: Автоматическое создание тегов ====================
@receiver(post_save, sender=TimelineEvent)
def auto_extract_tags(sender, instance, created, **kwargs):
    """
    Автоматически извлекает теги из описания события.
    """
    if created and not instance.tags:
        # Простой алгоритм извлечения ключевых слов
        keywords = []
        text = f"{instance.title} {instance.description}".lower()

        # Список математических терминов для автоматического тегирования
        math_terms = [
            'теорема', 'уравнение', 'функция', 'интеграл', 'производная',
            'алгебра', 'геометрия', 'тригонометрия', 'анализ', 'дифференциал',
            'матрица', 'вероятность', 'статистика', 'число', 'формула',
            'доказательство', 'аксиома', 'гипотеза', 'модель', 'алгоритм'
        ]

        for term in math_terms:
            if term in text:
                keywords.append(term)

        if keywords:
            instance.tags = ', '.join(keywords[:5])  # максимум 5 тегов
            instance.save(update_fields=['tags'])
            logger.info(f"Автоматически добавлены теги: {instance.tags}")


# ==================== SIGNAL 4: Уведомления при лайках ====================
@receiver(post_save, sender=TimelineLike)
def notify_timeline_like(sender, instance, created, **kwargs):
    """
    Отправляет уведомление владельцу таймлайна при новом лайке.
    """
    if created:
        timeline = instance.timeline
        liker = instance.user

        # Проверяем, что это не владелец лайкнул свой таймлайн
        if liker != timeline.created_by:
            # Логируем событие (в будущем можно добавить email/Telegram)
            logger.info(f"Пользователь {liker.username} лайкнул таймлайн '{timeline.title}'")

            # Можно добавить здесь отправку реального уведомления:
            # send_email_notification(timeline.created_by, f"Ваш таймлайн лайкнули!")
            # или
            # send_telegram_notification(timeline.created_by, "Новый лайк!")


# ==================== SIGNAL 5: Проверка дубликатов событий ====================
@receiver(pre_save, sender=TimelineEvent)
def prevent_duplicate_events(sender, instance, **kwargs):
    """
    Предотвращает создание дубликатов событий в одном таймлайне.
    """
    if instance.pk is None:  # только для новых событий
        duplicate = TimelineEvent.objects.filter(
            timeline=instance.timeline,
            title__iexact=instance.title,
            year=instance.year
        ).exists()

        if duplicate:
            raise ValueError(
                f"Событие '{instance.title}' ({instance.year}) уже существует в этом таймлайне!"
            )


# ==================== SIGNAL 6: Очистка кэша при изменении таймлайна ====================
@receiver(post_save, sender=Timeline)
@receiver(post_delete, sender=Timeline)
def clear_timeline_cache(sender, instance, **kwargs):
    """
    Очищает кэш при изменении таймлайна.
    """
    # Удаляем все ключи кэша, связанные с этим таймлайном
    cache.delete_many([
        f'timeline_{instance.pk}',
        f'timeline_stats_{instance.pk}',
        'recent_timelines',
        'popular_timelines',
        f'timeline_events_{instance.pk}'
    ])
    logger.info(f"Кэш очищен для таймлайна #{instance.pk}")