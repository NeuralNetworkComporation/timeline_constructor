from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import login
from .models import Timeline, TimelineEvent
from .forms import TimelineForm, TimelineEventForm


def home(request):
    """Главная страница"""
    public_timelines = Timeline.objects.filter(is_public=True)[:6]
    return render(request, 'home.html', {'public_timelines': public_timelines})


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
    return render(request, 'dashboard.html', {'timelines': user_timelines})


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
def event_create(request, timeline_pk):
    """Добавление события к таймлайну"""
    timeline = get_object_or_404(Timeline, pk=timeline_pk, created_by=request.user)

    if request.method == 'POST':
        form = TimelineEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.timeline = timeline
            event.save()
            messages.success(request, 'Событие добавлено!')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')

    return redirect('timeline_edit', pk=timeline_pk)


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
        timeline.delete()
        messages.success(request, 'Таймлайн успешно удален!')
        return redirect('dashboard')

    return render(request, 'timeline_confirm_delete.html', {'timeline': timeline})


def timeline_detail(request, pk):
    """Просмотр таймлайна"""
    timeline = get_object_or_404(Timeline, pk=pk)
    if not timeline.is_public and timeline.created_by != request.user:
        messages.error(request, 'У вас нет доступа к этому таймлайну.')
        return redirect('home')

    events = timeline.events.all()
    return render(request, 'timeline_view.html', {'timeline': timeline, 'events': events})


def timeline_list(request):
    """Список всех публичных таймлайнов"""
    timelines = Timeline.objects.filter(is_public=True)
    return render(request, 'timeline_list.html', {'timelines': timelines})