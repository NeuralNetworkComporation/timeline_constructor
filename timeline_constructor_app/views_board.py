from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models_board import BoardTimeline, BoardConnection
from .forms_board import BoardTimelineForm


@login_required
def board_view(request):
    """Основное представление доски"""
    timelines = BoardTimeline.objects.filter(created_by=request.user)
    connections = BoardConnection.objects.filter(
        source__created_by=request.user
    )

    return render(request, 'board/board_new.html', {
        'timelines': timelines,
        'connections': connections
    })


@csrf_exempt
@login_required
def create_board_timeline(request):
    """Создание таймлайна на доске (AJAX)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            timeline = BoardTimeline.objects.create(
                title=data.get('title', 'Новый таймлайн'),
                description=data.get('description', ''),
                created_by=request.user,
                x=data.get('x', 100),
                y=data.get('y', 100),
                color=data.get('color', '#10b981')
            )

            return JsonResponse({
                'success': True,
                'timeline': {
                    'id': timeline.id,
                    'title': timeline.title,
                    'description': timeline.description,
                    'x': timeline.x,
                    'y': timeline.y,
                    'color': timeline.color
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@csrf_exempt
@login_required
def update_timeline_position(request, pk):
    """Обновление позиции таймлайна"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            timeline = get_object_or_404(BoardTimeline, pk=pk, created_by=request.user)

            timeline.x = data.get('x', timeline.x)
            timeline.y = data.get('y', timeline.y)
            timeline.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@csrf_exempt
@login_required
def delete_board_timeline(request, pk):
    """Удаление таймлайна с доски"""
    if request.method == 'POST':
        try:
            timeline = get_object_or_404(BoardTimeline, pk=pk, created_by=request.user)
            timeline.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@csrf_exempt
@login_required
def create_connection(request):
    """Создание соединения между таймлайнами"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            source = get_object_or_404(BoardTimeline, pk=data['source'], created_by=request.user)
            target = get_object_or_404(BoardTimeline, pk=data['target'], created_by=request.user)

            # Проверяем, не пытаемся ли соединить с собой
            if source.id == target.id:
                return JsonResponse({'success': False, 'error': 'Нельзя соединить с самим собой'})

            # Проверяем, существует ли уже соединение
            existing = BoardConnection.objects.filter(source=source, target=target)
            if existing.exists():
                return JsonResponse({'success': False, 'error': 'Соединение уже существует'})

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
                    'color': connection.color
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})