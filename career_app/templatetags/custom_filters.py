from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Возвращает элемент из словаря по ключу"""
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None

@register.filter
def dictsort(queryset, attribute):
    """Сортирует queryset и преобразует в словарь"""
    return {getattr(obj, 'id'): obj for obj in queryset}


@register.filter
def percentage(value, total):
    """Рассчитывает процент"""
    try:
        if total == 0:
            return 0
        return round((value / total) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def growth_rate(current, previous):
    """Рассчитывает рост в процентах"""
    try:
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0