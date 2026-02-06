import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import BoardTimeline, BoardConnection, BoardSettings


@login_required
def board_view(request):
    """Основное представление доски"""
    # Получаем или создаем настройки
    settings, created = BoardSettings.objects.get_or_create(user=request.user)

    # Получаем все таймлайны пользователя
    timelines = BoardTimeline.objects.filter(user=request.user)

    # Получаем все соединения
    connections = BoardConnection.objects.filter(source__user=request.user)

    return render(request, 'board/board.html', {
        'timelines': timelines,
        'connections': connections,
        'settings': settings,
    })


@csrf_exempt
@login_required
def create_timeline(request):
    """Создание таймлайна на доске"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            timeline = BoardTimeline.objects.create(
                title=data.get('title', 'Новый таймлайн'),
                description=data.get('description', ''),
                user=request.user,
                x=float(data.get('x', 100)),
                y=float(data.get('y', 100)),
                color=data.get('color', '#10b981'),
                background_color=data.get('background_color', '#ffffff'),
                border_color=data.get('border_color', '#10b981')
            )

            return JsonResponse({
                'success': True,
                'timeline': {
                    'id': timeline.id,
                    'title': timeline.title,
                    'x': timeline.x,
                    'y': timeline.y,
                    'color': timeline.color,
                    'background_color': timeline.background_color,
                    'border_color': timeline.border_color,
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@csrf_exempt
@login_required
def update_timeline_position(request, timeline_id):
    """Обновление позиции таймлайна"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            timeline = get_object_or_404(BoardTimeline, id=timeline_id, user=request.user)

            timeline.x = float(data.get('x', timeline.x))
            timeline.y = float(data.get('y', timeline.y))
            timeline.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@csrf_exempt
@login_required
def delete_timeline(request, timeline_id):
    """Удаление таймлайна"""
    if request.method == 'DELETE':
        try:
            timeline = get_object_or_404(BoardTimeline, id=timeline_id, user=request.user)
            timeline.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@csrf_exempt
@login_required
def create_connection(request):
    """Создание соединения"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            source_id = data['source']
            target_id = data['target']

            if source_id == target_id:
                return JsonResponse({'success': False, 'error': 'Нельзя соединить с самим собой'})

            source = get_object_or_404(BoardTimeline, id=source_id, user=request.user)
            target = get_object_or_404(BoardTimeline, id=target_id, user=request.user)

            connection = BoardConnection.objects.create(
                source=source,
                target=target,
                color=data.get('color', '#3b82f6')
            )

            return JsonResponse({
                'success': True,
                'connection': {
                    'id': connection.id,
                    'source': source.id,
                    'target': target.id,
                    'color': connection.color,
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@csrf_exempt
@login_required
def save_board_state(request):
    """Сохранение состояния доски"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            settings = BoardSettings.objects.get(user=request.user)

            settings.last_view_x = float(data.get('x', settings.last_view_x))
            settings.last_view_y = float(data.get('y', settings.last_view_y))
            settings.last_zoom = float(data.get('zoom', settings.last_zoom))
            settings.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})