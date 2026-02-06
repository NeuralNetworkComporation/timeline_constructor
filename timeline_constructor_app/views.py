import math
import json
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
import base64
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from datetime import datetime
from .models import Timeline, TimelineEvent, TimelineComment, TimelineLike, TimelineView, BoardNode, BoardConnection
from .forms import TimelineForm, TimelineEventForm, TimelineCommentForm, TimelineSearchForm, TimelineSettingsForm, \
    TimelineImportForm
from functools import wraps


def home(request):
    """Главная страница"""
    public_timelines = Timeline.objects.filter(is_public=True)[:6]

    # Добавляем данные для FAQ
    from django.contrib.auth.models import User
    from django.db.models import Count

    timelines_count = Timeline.objects.filter(is_public=True).count()
    events_count = TimelineEvent.objects.count()
    users_count = User.objects.count()

    return render(request, 'home.html', {
        'public_timelines': public_timelines,
        'timelines_count': timelines_count,
        'events_count': events_count,
        'users_count': users_count,
    })


def timeline_statistics(request):
    """Статистика по таймлайнам"""
    # Общая статистика
    total_timelines = Timeline.objects.count()
    total_events = TimelineEvent.objects.count()
    total_views = TimelineView.objects.count()
    user_count = User.objects.count()

    # Популярные таймлайны (по просмотрам)
    popular_timelines = Timeline.objects.filter(is_public=True).annotate(
        views_count=Count('views'),
        likes_count=Count('likes'),
        events_count=Count('events')
    ).order_by('-views_count')[:10]

    # Недавние таймлайны
    recent_timelines = Timeline.objects.filter(is_public=True).order_by('-created_at')[:10]

    # Статистика по эпохам
    era_stats = TimelineEvent.objects.values('era').annotate(
        count=Count('id')
    ).order_by('-count')

    # Дополнительная статистика
    public_timelines = Timeline.objects.filter(is_public=True).count()
    public_percentage = (public_timelines / total_timelines * 100) if total_timelines > 0 else 0

    # Среднее количество событий
    avg_events = round(total_events / total_timelines, 1) if total_timelines > 0 else 0

    # Активные пользователи (создали хотя бы один таймлайн)
    active_users = User.objects.annotate(
        timeline_count=Count('timeline')
    ).filter(timeline_count__gt=0).count()

    return render(request, 'timeline_statistics.html', {
        'total_timelines': total_timelines,
        'total_events': total_events,
        'total_views': total_views,
        'user_count': user_count,
        'popular_timelines': popular_timelines,
        'recent_timelines': recent_timelines,
        'era_stats': era_stats,
        'public_percentage': round(public_percentage, 1),
        'avg_events': avg_events,
        'active_users': active_users,
    })

def signup(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Аккаунт {user.username} создан!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def dashboard(request):
    """Личный кабинет пользователя"""
    user_timelines = Timeline.objects.filter(created_by=request.user)
    total_events = TimelineEvent.objects.filter(timeline__created_by=request.user).count()
    public_timelines_count = user_timelines.filter(is_public=True).count()

    # Последние просмотры
    recent_views = TimelineView.objects.filter(
        timeline__created_by=request.user
    ).select_related('timeline', 'user').order_by('-viewed_at')[:5]

    return render(request, 'dashboard.html', {
        'timelines': user_timelines,
        'total_events': total_events,
        'public_timelines_count': public_timelines_count,
        'recent_views': recent_views
    })


@login_required
def timeline_create(request):
    """Создание нового таймлайна"""
    if request.method == 'POST':
        form = TimelineForm(request.POST)
        if form.is_valid():
            timeline = form.save(commit=False)
            timeline.created_by = request.user
            timeline.save()
            messages.success(request, 'Таймлайн успешно создан!')
            return redirect('timeline_edit', pk=timeline.pk)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = TimelineForm()

    return render(request, 'timeline_form.html', {'form': form, 'title': 'Создать таймлайн'})


@login_required
def timeline_edit(request, pk):
    """Редактирование таймлайна"""
    timeline = get_object_or_404(Timeline, pk=pk, created_by=request.user)
    events = timeline.events.all()

    if request.method == 'POST':
        form = TimelineForm(request.POST, instance=timeline)
        if form.is_valid():
            form.save()
            messages.success(request, 'Таймлайн обновлен!')
            return redirect('timeline_edit', pk=timeline.pk)
    else:
        form = TimelineForm(instance=timeline)

    event_form = TimelineEventForm()

    return render(request, 'timeline_edit.html', {
        'timeline': timeline,
        'form': form,
        'events': events,
        'event_form': event_form
    })


@login_required
def timeline_settings(request, pk):
    """Настройки таймлайна"""
    timeline = get_object_or_404(Timeline, pk=pk, created_by=request.user)

    if request.method == 'POST':
        form = TimelineSettingsForm(request.POST, instance=timeline)
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки таймлайна обновлены!')
            return redirect('timeline_settings', pk=timeline.pk)
    else:
        form = TimelineSettingsForm(instance=timeline)

    return render(request, 'timeline_settings.html', {
        'timeline': timeline,
        'form': form
    })


@login_required
def event_create(request, timeline_pk):
    """Добавление события к таймлайну"""
    timeline = get_object_or_404(Timeline, pk=timeline_pk, created_by=request.user)

    if request.method == 'POST':
        form = TimelineEventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.timeline = timeline
            event.save()
            messages.success(request, 'Событие добавлено!')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')

    return redirect('timeline_edit', pk=timeline_pk)


@login_required
def event_edit(request, pk):
    """Редактирование события"""
    event = get_object_or_404(TimelineEvent, pk=pk, timeline__created_by=request.user)

    if request.method == 'POST':
        form = TimelineEventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Событие обновлено!')
            return redirect('timeline_edit', pk=event.timeline.pk)
    else:
        form = TimelineEventForm(instance=event)

    return render(request, 'event_edit.html', {
        'form': form,
        'event': event,
        'timeline': event.timeline
    })


@login_required
def event_delete(request, pk):
    """Удаление события"""
    event = get_object_or_404(TimelineEvent, pk=pk, timeline__created_by=request.user)
    timeline_pk = event.timeline.pk
    event.delete()
    messages.success(request, 'Событие удалено!')
    return redirect('timeline_edit', pk=timeline_pk)


@login_required
def timeline_delete(request, pk):
    """Удаление таймлайна"""
    timeline = get_object_or_404(Timeline, pk=pk, created_by=request.user)

    if request.method == 'POST':
        timeline_title = timeline.title
        timeline.delete()
        messages.success(request, f'Таймлайн "{timeline_title}" успешно удален!')
        return redirect('dashboard')

    return render(request, 'timeline_confirm_delete.html', {'timeline': timeline})


def timeline_detail(request, pk):
    """Просмотр таймлайна с отслеживанием просмотров"""
    timeline = get_object_or_404(Timeline, pk=pk)

    # Проверка доступа
    if not timeline.is_public and (not request.user.is_authenticated or timeline.created_by != request.user):
        messages.error(request, 'У вас нет доступа к этому таймлайну.')
        return redirect('home')

    # Отслеживание просмотра
    if request.user.is_authenticated:
        TimelineView.objects.get_or_create(
            timeline=timeline,
            user=request.user,
            defaults={'ip_address': get_client_ip(request)}
        )
    else:
        TimelineView.objects.create(
            timeline=timeline,
            ip_address=get_client_ip(request)
        )

    events = timeline.events.all()

    # Добавляем RGB значения для CSS
    color_rgb = {
        'green': '16, 185, 129',
        'blue': '59, 130, 246',
        'purple': '139, 92, 246',
        'orange': '249, 115, 22',
        'red': '239, 68, 68',
        'teal': '20, 184, 166',
    }

    return render(request, 'timeline_view.html', {
        'timeline': timeline,
        'events': events,
        'color_rgb': color_rgb.get(timeline.color_scheme, '16, 185, 129'),
    })


@login_required
def like_timeline(request, pk):
    """Лайк/анлайк таймлайна"""
    timeline = get_object_or_404(Timeline, pk=pk)

    if timeline.likes.filter(user=request.user).exists():
        timeline.likes.filter(user=request.user).delete()
        liked = False
        message = 'Лайк удален'
    else:
        TimelineLike.objects.create(timeline=timeline, user=request.user)
        liked = True
        message = 'Таймлайну понравилось'

    likes_count = timeline.likes.count()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'likes_count': likes_count,
            'message': message
        })

    messages.success(request, message)
    return redirect('timeline_detail', pk=timeline.pk)


@login_required
def add_comment(request, pk):
    """Добавление комментария"""
    timeline = get_object_or_404(Timeline, pk=pk)

    if not timeline.allow_comments:
        messages.error(request, 'Комментарии к этому таймлайну запрещены.')
        return redirect('timeline_detail', pk=timeline.pk)

    if request.method == 'POST':
        form = TimelineCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.timeline = timeline
            comment.user = request.user
            comment.save()
            messages.success(request, 'Комментарий добавлен!')

    return redirect('timeline_detail', pk=timeline.pk)


def timeline_list(request):
    """Список всех публичных таймлайнов"""
    timelines = Timeline.objects.filter(is_public=True).annotate(
        events_count=Count('events'),
        likes_count=Count('likes'),
        views_count=Count('views')
    ).order_by('-created_at')

    # Пагинация
    paginator = Paginator(timelines, 12)
    page = request.GET.get('page')
    timelines_page = paginator.get_page(page)

    return render(request, 'timeline_list.html', {
        'timelines': timelines_page
    })


def timeline_search(request):
    """Расширенный поиск таймлайнов"""
    form = TimelineSearchForm(request.GET or None)
    timelines = Timeline.objects.filter(is_public=True).annotate(
        events_count=Count('events')
    )

    search_performed = False

    if form.is_valid():
        query = form.cleaned_data.get('query')
        era = form.cleaned_data.get('era')
        event_type = form.cleaned_data.get('event_type')
        min_year = form.cleaned_data.get('min_year')
        max_year = form.cleaned_data.get('max_year')

        if any([query, era, event_type, min_year, max_year]):
            search_performed = True

        if query:
            timelines = timelines.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(events__title__icontains=query) |
                Q(events__description__icontains=query) |
                Q(events__tags__icontains=query)
            ).distinct()

        if era:
            timelines = timelines.filter(events__era=era).distinct()

        if event_type:
            timelines = timelines.filter(events__event_type=event_type).distinct()

        if min_year:
            timelines = timelines.filter(events__year__gte=min_year).distinct()

        if max_year:
            timelines = timelines.filter(events__year__lte=max_year).distinct()

    # Пагинация
    paginator = Paginator(timelines, 12)
    page = request.GET.get('page')
    timelines_page = paginator.get_page(page)

    return render(request, 'timeline_search.html', {
        'form': form,
        'timelines': timelines_page,
        'search_performed': search_performed
    })


@login_required
def timeline_export(request, pk):
    """Экспорт таймлайна в JSON файл"""
    timeline = get_object_or_404(Timeline, pk=pk, created_by=request.user)

    events_data = []
    for event in timeline.events.all():
        event_data = {
            'title': event.title,
            'description': event.description,
            'detailed_description': event.detailed_description,
            'year': event.year,
            'era': event.era,
            'event_type': event.event_type,
            'importance': event.importance,
            'location': event.location,
            'tags': event.tags,
            'source_link': event.source_link,
        }

        if event.month:
            event_data['month'] = event.month
        if event.day:
            event_data['day'] = event.day
        if event.image:
            event_data['image'] = request.build_absolute_uri(event.image.url)

        events_data.append(event_data)

    data = {
        'title': timeline.title,
        'description': timeline.description,
        'settings': {
            'color_scheme': timeline.color_scheme,
            'layout': timeline.layout,
            'show_dates': timeline.show_dates,
            'show_images': timeline.show_images,
        },
        'events': events_data,
        'exported_at': datetime.now().isoformat(),
        'exported_by': request.user.username,
    }

    # Важно: используем HttpResponse с правильными заголовками
    import json
    response = HttpResponse(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type='application/json; charset=utf-8'
    )

    # Безопасное имя файла
    import re
    filename = re.sub(r'[^\w\s-]', '', timeline.title.strip())
    filename = re.sub(r'[-\s]+', '_', filename)
    if not filename:
        filename = f'timeline_{pk}'

    response['Content-Disposition'] = f'attachment; filename="{filename}.json"'
    response['X-Content-Type-Options'] = 'nosniff'

    return response


@login_required
def timeline_import(request):
    """Импорт таймлайна из JSON"""
    # Декоратор @login_required уже проверяет авторизацию
    # Но добавим явную проверку для ясности
    if not request.user.is_authenticated:
        messages.warning(request, 'Для импорта таймлайнов необходимо войти в систему.')
        return redirect('login')

    if request.method == 'POST':
        form = TimelineImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                json_file = request.FILES['json_file']
                data = json.loads(json_file.read().decode('utf-8'))

                # Создаем новый таймлайн
                timeline = Timeline.objects.create(
                    title=f"{data['title']} (импорт)",
                    description=data.get('description', ''),
                    created_by=request.user,
                    is_public=False,
                    color_scheme=data.get('settings', {}).get('color_scheme', 'green'),
                    layout=data.get('settings', {}).get('layout', 'vertical'),
                )

                # Импортируем события
                for event_data in data.get('events', []):
                    TimelineEvent.objects.create(
                        timeline=timeline,
                        title=event_data['title'],
                        description=event_data['description'],
                        detailed_description=event_data.get('detailed_description', ''),
                        year=event_data['year'],
                        month=event_data.get('month'),
                        day=event_data.get('day'),
                        era=event_data.get('era', 'event'),
                        event_type=event_data.get('event_type', 'event'),
                        importance=event_data.get('importance', 2),
                        location=event_data.get('location', ''),
                        tags=event_data.get('tags', ''),
                        source_link=event_data.get('source_link', ''),
                    )

                messages.success(request, 'Таймлайн успешно импортирован!')
                return redirect('timeline_edit', pk=timeline.pk)

            except Exception as e:
                messages.error(request, f'Ошибка импорта: {str(e)}')
    else:
        form = TimelineImportForm()

    return render(request, 'timeline_import.html', {'form': form})


@login_required
def timeline_duplicate(request, pk):
    """Дублирование таймлайна"""
    original = get_object_or_404(Timeline, pk=pk)

    if not original.is_public and original.created_by != request.user:
        messages.error(request, 'У вас нет доступа к этому таймлайну.')
        return redirect('home')

    # Создаем копию
    new_timeline = Timeline.objects.create(
        title=f"{original.title} (копия)",
        description=original.description,
        created_by=request.user,
        is_public=False,
        color_scheme=original.color_scheme,
        layout=original.layout,
        show_dates=original.show_dates,
        show_images=original.show_images,
        allow_comments=original.allow_comments,
    )

    # Копируем события
    for event in original.events.all():
        new_event = TimelineEvent.objects.create(
            timeline=new_timeline,
            title=event.title,
            description=event.description,
            detailed_description=event.detailed_description,
            year=event.year,
            month=event.month,
            day=event.day,
            era=event.era,
            event_type=event.event_type,
            importance=event.importance,
            source_link=event.source_link,
            location=event.location,
            tags=event.tags,
        )
        # Копируем изображение если есть
        if event.image:
            new_event.image.save(event.image.name, event.image.file, save=True)

    messages.success(request, 'Таймлайн успешно скопирован!')
    return redirect('timeline_edit', pk=new_timeline.pk)


def timeline_statistics(request):
    """Статистика по таймлайнам"""
    popular_timelines = Timeline.objects.filter(is_public=True).annotate(
        views_count=Count('views'),
        likes_count=Count('likes'),
        events_count=Count('events')
    ).order_by('-views_count')[:10]

    recent_timelines = Timeline.objects.filter(is_public=True).order_by('-created_at')[:10]

    # Статистика по эпохам
    era_stats = TimelineEvent.objects.values('era').annotate(
        count=Count('id')
    ).order_by('-count')

    total_timelines = Timeline.objects.filter(is_public=True).count()
    total_events = TimelineEvent.objects.count()
    total_views = TimelineView.objects.count()

    return render(request, 'timeline_statistics.html', {
        'popular_timelines': popular_timelines,
        'recent_timelines': recent_timelines,
        'era_stats': era_stats,
        'total_timelines': total_timelines,
        'total_events': total_events,
        'total_views': total_views,
    })


# Вспомогательная функция для получения IP
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def timeline_export_download(request, pk):
    """Перенаправление на экспорт с авто-скачиванием"""
    return redirect('timeline_export', pk=pk)

def login_required_with_redirect(view_func):
    """Декоратор с перенаправлением на страницу входа"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Сохраняем URL, куда пользователь хотел попасть
            next_url = request.get_full_path()
            messages.info(request, 'Для доступа к этой странице необходимо войти в систему.')
            return redirect(f'{reverse("login")}?next={next_url}')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_required
def board_view(request):
    """Исправленная версия доски"""
    # Получаем таймлайны пользователя
    timelines = Timeline.objects.filter(created_by=request.user)

    # Создаем начальные позиции для таймлайнов без координат
    for i, timeline in enumerate(timelines):
        if timeline.board_x == 0 and timeline.board_y == 0:
            timeline.board_x = 100 + (i % 5) * 300  # Располагаем в сетке
            timeline.board_y = 100 + (i // 5) * 200
            timeline.save()

    return render(request, 'board/board_fixed.html', {
        'timelines': timelines,
        'grid_size': 50
    })


@login_required
def update_timeline_position(request, pk):
    """Обновление позиции таймлайна на доске"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            timeline = get_object_or_404(Timeline, pk=pk, created_by=request.user)

            timeline.board_x = data.get('x', timeline.board_x)
            timeline.board_y = data.get('y', timeline.board_y)
            timeline.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def timeline_create_modal(request):
    """Форма создания таймлайна для модального окна"""
    if request.method == 'POST':
        form = TimelineForm(request.POST)
        if form.is_valid():
            timeline = form.save(commit=False)
            timeline.created_by = request.user

            # Позиция из формы
            timeline.board_x = request.POST.get('position_x', 0)
            timeline.board_y = request.POST.get('position_y', 0)

            timeline.save()

            return JsonResponse({
                'success': True,
                'redirect': reverse('board')
            })

    else:
        form = TimelineForm()

    return render(request, 'board/timeline_create_modal.html', {'form': form})


@login_required
def toggle_timeline_lock(request, pk):
    """Переключение блокировки таймлайна на доске"""
    if request.method == 'POST':
        timeline = get_object_or_404(Timeline, pk=pk, created_by=request.user)
        timeline.board_locked = not timeline.board_locked
        timeline.save()

        return JsonResponse({
            'success': True,
            'locked': timeline.board_locked,
            'message': 'Таймлайн заблокирован' if timeline.board_locked else 'Таймлайн разблокирован'
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def arrange_children(request, pk):
    """Автоматическое расположение дочерних таймлайнов"""
    if request.method == 'POST':
        parent = get_object_or_404(Timeline, pk=pk, created_by=request.user)
        children = Timeline.objects.filter(parent=parent, created_by=request.user)

        # Располагаем по кругу вокруг родителя
        positions = []
        center_x = parent.board_x
        center_y = parent.board_y
        radius = 300
        angle_step = 2 * math.pi / max(1, children.count())

        for i, child in enumerate(children):
            angle = i * angle_step
            x = center_x + radius * math.cos(angle) - 110  # Смещение на половину ширины узла
            y = center_y + radius * math.sin(angle) - 70  # Смещение на половину высоты узла

            child.board_x = x
            child.board_y = y
            child.save()

            positions.append({
                'id': child.id,
                'x': x,
                'y': y
            })

        return JsonResponse({
            'success': True,
            'positions': positions,
            'message': f'Расположено {len(positions)} дочерних таймлайнов'
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def create_connection(request):
    """Создание соединения между таймлайнами на доске"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            source_id = data.get('source')
            target_id = data.get('target')

            if source_id == target_id:
                return JsonResponse({'success': False, 'error': 'Нельзя соединить таймлайн с самим собой'})

            source = get_object_or_404(Timeline, pk=source_id, created_by=request.user)
            target = get_object_or_404(Timeline, pk=target_id, created_by=request.user)

            # Проверяем, существует ли уже такое соединение
            if BoardConnection.objects.filter(source=source, target=target).exists():
                return JsonResponse({'success': False, 'error': 'Соединение уже существует'})

            # Создаем соединение
            connection = BoardConnection.objects.create(
                source=source,
                target=target
            )

            return JsonResponse({
                'success': True,
                'connection': {
                    'id': connection.id,
                    'source': source.id,
                    'target': target.id
                },
                'message': 'Соединение создано'
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def timeline_create_connected(request, parent_id):
    """Создание связанного таймлайна"""
    parent = get_object_or_404(Timeline, pk=parent_id, created_by=request.user)

    if request.method == 'POST':
        form = TimelineForm(request.POST)
        if form.is_valid():
            timeline = form.save(commit=False)
            timeline.created_by = request.user
            timeline.parent = parent  # Устанавливаем родителя

            # Позиция рядом с родителем
            timeline.board_x = request.POST.get('position_x', parent.board_x + 250)
            timeline.board_y = request.POST.get('position_y', parent.board_y)

            timeline.save()

            # Создаем соединение
            BoardConnection.objects.create(source=parent, target=timeline)

            messages.success(request, 'Связанный таймлайн создан!')
            return redirect('board')

    else:
        form = TimelineForm()

    return render(request, 'board/timeline_create_connected.html', {
        'form': form,
        'parent': parent
    })


@login_required
def timeline_duplicate_board(request, pk):
    """Дублирование таймлайна на доске"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            original = get_object_or_404(Timeline, pk=pk, created_by=request.user)

            # Смещение для дубликата
            offset_x = data.get('offset_x', 50)
            offset_y = data.get('offset_y', 50)

            # Создаем копию
            new_timeline = Timeline.objects.create(
                title=f"{original.title} (копия)",
                description=original.description,
                created_by=request.user,
                is_public=False,
                color_scheme=original.color_scheme,
                layout=original.layout,
                show_dates=original.show_dates,
                show_images=original.show_images,
                allow_comments=original.allow_comments,
                board_x=original.board_x + offset_x,
                board_y=original.board_y + offset_y
            )

            # Копируем события
            for event in original.events.all():
                new_event = TimelineEvent.objects.create(
                    timeline=new_timeline,
                    title=event.title,
                    description=event.description,
                    detailed_description=event.detailed_description,
                    year=event.year,
                    month=event.month,
                    day=event.day,
                    era=event.era,
                    event_type=event.event_type,
                    importance=event.importance,
                    source_link=event.source_link,
                    location=event.location,
                    tags=event.tags,
                )
                # Копируем изображение если есть
                if event.image:
                    new_event.image.save(event.image.name, event.image.file, save=True)

            return JsonResponse({
                'success': True,
                'new_id': new_timeline.id,
                'message': 'Таймлайн продублирован'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def board(request):
    """Простая интерактивная доска"""
    # Получаем все узлы пользователя
    nodes = BoardNode.objects.filter(user=request.user)

    # Получаем все соединения
    connections = BoardConnection.objects.filter(from_node__user=request.user)

    return render(request, 'board/simple_board.html', {
        'nodes': nodes,
        'connections': connections
    })


@csrf_exempt
@login_required
def create_board_node(request):
    """Создание узла на доске (AJAX)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            node = BoardNode.objects.create(
                title=data.get('title', 'Новый узел'),
                description=data.get('description', ''),
                user=request.user,
                x=float(data.get('x', 100)),
                y=float(data.get('y', 100)),
                color=data.get('color', '#10b981'),
                bg_color=data.get('bg_color', '#ffffff')
            )

            return JsonResponse({
                'success': True,
                'node': {
                    'id': node.id,
                    'title': node.title,
                    'x': node.x,
                    'y': node.y,
                    'color': node.color,
                    'bg_color': node.bg_color
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@csrf_exempt
@login_required
def update_board_node(request, node_id):
    """Обновление позиции узла на доске"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            timeline = get_object_or_404(Timeline, id=node_id, created_by=request.user)

            timeline.board_x = float(data.get('x', timeline.board_x))
            timeline.board_y = float(data.get('y', timeline.board_y))
            timeline.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@csrf_exempt
@login_required
def delete_board_node(request, node_id):
    """Удаление узла с доски"""
    if request.method == 'POST':
        try:
            timeline = get_object_or_404(Timeline, id=node_id, created_by=request.user)
            timeline.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def board_create_timeline(request):
    """Создание таймлайна прямо на доске"""
    if request.method == 'POST':
        form = TimelineForm(request.POST)
        if form.is_valid():
            timeline = form.save(commit=False)
            timeline.created_by = request.user

            # Позиция в центре видимой области
            board_x = request.POST.get('board_x', 300)
            board_y = request.POST.get('board_y', 200)

            timeline.board_x = float(board_x)
            timeline.board_y = float(board_y)

            timeline.save()

            return JsonResponse({
                'success': True,
                'timeline_id': timeline.id,
                'title': timeline.title,
                'board_x': timeline.board_x,
                'board_y': timeline.board_y
            })

    return JsonResponse({'success': False, 'error': 'Invalid request'})