from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db import models
from django.db.models import Q, Count, Avg, Case, When, FloatField, F
from django.core.paginator import Paginator
from .models import *
from .forms import *
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils import timezone
from datetime import timedelta
import random
from django.db.models import Q, Count, Avg, Case, When, FloatField, F
from django.db.models.functions import TruncDay, TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Category
from django.db.models.functions import Cast  # Добавляем импорт Cast
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db import models
from django.db.models import Q, Count, Avg, Case, When, FloatField, F
from django.db.models.functions import Cast
from django.core.paginator import Paginator
from .models import *
from .forms import *
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from django.utils import timezone
from datetime import timedelta
import json
import pandas as pd
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import datetime

def get_subcategories(request):
    main_category_id = request.GET.get('main_category_id')
    if main_category_id:
        try:
            main_category = get_object_or_404(Category, id=main_category_id)
            subcategories = Category.objects.filter(parent=main_category).order_by('name')
            data = {
                'subcategories': [
                    {'id': cat.id, 'name': cat.name}
                    for cat in subcategories
                ]
            }
            return JsonResponse(data)
        except:
            return JsonResponse({'subcategories': []})
    return JsonResponse({'subcategories': []})


@require_GET
def get_skills(request):
    """AJAX view для получения навыков подкатегории"""
    subcategory_id = request.GET.get('subcategory_id')

    if subcategory_id:
        skills = SkillTag.objects.filter(category_id=subcategory_id)
        data = {
            'skills': [
                {'id': skill.id, 'name': skill.name}
                for skill in skills
            ]
        }
    else:
        data = {'skills': []}

    return JsonResponse(data)

def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Получаем или создаем профиль пользователя
            role = form.cleaned_data['role']

            try:
                # Пытаемся получить существующий профиль
                user_profile = user.userprofile
                # Обновляем роль
                user_profile.role = role
                user_profile.save()
            except UserProfile.DoesNotExist:
                # Создаем новый профиль если не существует
                user_profile = UserProfile.objects.create(user=user, role=role)

            # Для HR и университетов создаем запрос на подтверждение
            if role in ['hr', 'university']:
                company_name = form.cleaned_data.get('company_name', '')
                institution_name = form.cleaned_data.get('institution_name', '')

                RoleApprovalRequest.objects.create(
                    user=user,
                    requested_role=role,
                    company_name=company_name,
                    institution_name=institution_name
                )

                # Создаем компанию или учебное заведение
                if role == 'hr' and company_name:
                    company = Company.objects.create(
                        name=company_name,
                        contact_email=user.email,
                        contact_phone='',
                        is_approved=False
                    )
                    user_profile.company = company
                    user_profile.save()

                elif role == 'university' and institution_name:
                    institution = EducationalInstitution.objects.create(
                        name=institution_name,
                        contact_email=user.email,
                        contact_phone='',
                        is_approved=False
                    )
                    user_profile.institution = institution
                    user_profile.save()

                messages.success(request,
                                 'Регистрация прошла успешно! Ваш аккаунт ожидает подтверждения администратором.')
                return redirect('pending_approval')

            else:  # Для соискателей
                # Создаем или обновляем профиль соискателя
                applicant, created = Applicant.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': user.first_name or '',
                        'last_name': user.last_name or '',
                        'email': user.email or ''
                    }
                )

                # Соискатели автоматически подтверждаются
                user_profile.is_approved = True
                user_profile.save()

                login(request, user)
                messages.success(request, 'Регистрация прошла успешно! Заполните ваш профиль.')
                return redirect('profile_setup')

    else:
        form = CustomUserCreationForm()

    context = {'form': form}
    return render(request, 'registration/register.html', context)

def is_admin(user):
    try:
        return user.userprofile.role == 'admin'  # Админы не требуют is_approved
    except UserProfile.DoesNotExist:
        return False

def is_hr(user):
    try:
        return user.userprofile.role == 'hr' and user.userprofile.is_approved
    except UserProfile.DoesNotExist:
        return False

def is_university(user):
    try:
        return user.userprofile.role == 'university' and user.userprofile.is_approved
    except UserProfile.DoesNotExist:
        return False


def home(request):
    try:
        vacancies = Vacancy.objects.filter(status='published')[:3]
        internships = Internship.objects.filter(status='published')[:3]

        # Создаем объединенный список для главной страницы
        recent_items = []

        for vacancy in vacancies:
            recent_items.append({
                'type': 'vacancy',
                'id': vacancy.id,
                'title': vacancy.title,
                'company': vacancy.company.name,
                'description': vacancy.description,
                'salary': vacancy.salary,
            })

        for internship in internships:
            recent_items.append({
                'type': 'internship',
                'id': internship.id,
                'title': internship.title,
                'company': internship.institution.name,
                'description': internship.description,
            })

        # Сортируем по дате (можно добавить дату создания)
        recent_items.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    except Exception as e:
        recent_items = []
        if settings.DEBUG:
            messages.info(request, f'Отладочная информация: {e}')

    context = {
        'recent_items': recent_items,
        'debug': settings.DEBUG,
    }
    return render(request, 'career_app/home.html', context)


def vacancy_list(request):
    # Получаем все опубликованные вакансии и стажировки
    vacancies = Vacancy.objects.filter(status='published')
    internships = Internship.objects.filter(status='published')

    # Параметры фильтрации из GET-запроса
    filter_type = request.GET.get('type', 'all')
    selected_categories = request.GET.getlist('category')  # Множественный выбор
    selected_main_categories = request.GET.getlist('main_category')  # Множественный выбор

    # Объединяем данные в один список с пометкой типа
    items = []

    # Добавляем вакансии
    for vacancy in vacancies:
        items.append({
            'type': 'vacancy',
            'object': vacancy,
            'title': vacancy.title,
            'company': vacancy.company.name,
            'description': vacancy.description,
            'salary': vacancy.salary,
            'category': vacancy.category,
            'created_at': vacancy.created_at,
            'id': vacancy.id,
        })

    # Добавляем стажировки
    for internship in internships:
        items.append({
            'type': 'internship',
            'object': internship,
            'title': internship.title,
            'company': internship.institution.name,
            'description': internship.description,
            'specialty': internship.specialty,
            'student_count': internship.student_count,
            'period': internship.period,
            'category': internship.category,
            'created_at': internship.created_at,
            'id': internship.id,
        })

    # Применяем фильтры
    if filter_type == 'vacancies':
        items = [item for item in items if item['type'] == 'vacancy']
    elif filter_type == 'internships':
        items = [item for item in items if item['type'] == 'internship']

    # Фильтр по основным категориям
    if selected_main_categories:
        main_category_ids = [int(cat_id) for cat_id in selected_main_categories]
        main_categories = Category.objects.filter(id__in=main_category_ids)
        subcategory_ids = []
        for main_cat in main_categories:
            subcategory_ids.extend([subcat.id for subcat in main_cat.get_subcategories()])
        items = [item for item in items if item['category'] and item['category'].id in subcategory_ids]

    # Фильтр по конкретным категориям
    if selected_categories and not selected_main_categories:
        category_ids = [int(cat_id) for cat_id in selected_categories]
        items = [item for item in items if item['category'] and item['category'].id in category_ids]

    # Поиск
    query = request.GET.get('q')
    if query:
        items = [item for item in items if
                 query.lower() in item['title'].lower() or
                 query.lower() in item['description'].lower() or
                 query.lower() in item['company'].lower()]

    # Сортировка по дате создания (новые сначала)
    items.sort(key=lambda x: x['created_at'], reverse=True)

    # Пагинация
    paginator = Paginator(items, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Получаем категории для фильтра
    main_categories = Category.objects.filter(is_main=True)
    all_categories = Category.objects.all()

    context = {
        'page_obj': page_obj,
        'query': query,
        'filter_type': filter_type,
        'selected_categories': [int(cat_id) for cat_id in selected_categories],
        'selected_main_categories': [int(cat_id) for cat_id in selected_main_categories],
        'main_categories': main_categories,
        'all_categories': all_categories,
        'total_count': len(items),
        'vacancies_count': len([item for item in items if item['type'] == 'vacancy']),
        'internships_count': len([item for item in items if item['type'] == 'internship']),
    }
    return render(request, 'career_app/vacancy_list.html', context)


def vacancy_detail(request, pk):
    try:
        vacancy = Vacancy.objects.get(pk=pk, status='published')
    except Vacancy.DoesNotExist:
        vacancy = get_object_or_404(Vacancy, pk=pk)
        can_view = False
        if request.user.is_authenticated:
            if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'hr':
                if vacancy.company == request.user.userprofile.company:
                    can_view = True
            if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin':
                can_view = True
        if not can_view:
            messages.error(request, 'У вас нет прав для просмотра этой вакансии или она еще не опубликована.')
            return redirect('vacancy_list')

    # Инициализируем переменные
    has_applied = False
    chat_thread = None
    applicant = None
    show_chat_button = False

    # Проверяем для авторизованных пользователей-соискателей
    if request.user.is_authenticated and hasattr(request.user,
                                                 'userprofile') and request.user.userprofile.role == 'applicant':
        try:
            applicant = request.user.applicant
            # Проверяем, откликался ли уже пользователь
            has_applied = Application.objects.filter(
                vacancy=vacancy,
                applicant=applicant
            ).exists()

            # Ищем существующий чат
            if has_applied:
                chat_thread = ChatThread.objects.filter(
                    vacancy=vacancy,
                    applicant=applicant,
                    is_active=True
                ).first()
                if chat_thread:
                    show_chat_button = True

        except Applicant.DoesNotExist:
            pass

    # Обработка POST запроса (отклик)
    if request.method == 'POST' and vacancy.status == 'published':
        if not request.user.is_authenticated:
            # Обработка для неавторизованных пользователей
            applicant_form = ApplicantForm(request.POST, request.FILES)
            if applicant_form.is_valid():
                applicant = applicant_form.save()
                application = Application.objects.create(
                    vacancy=vacancy,
                    applicant=applicant,
                    cover_letter=request.POST.get('cover_letter', '')
                )

                # Создаем чат сразу
                if vacancy.company and vacancy.company.userprofile_set.filter(role='hr').exists():
                    hr_user = vacancy.company.userprofile_set.filter(role='hr').first().user
                    chat_thread, created = ChatThread.get_or_create_chat(
                        vacancy=vacancy,
                        applicant=applicant,
                        hr_user=hr_user
                    )
                    if created:
                        ChatMessage.objects.create(
                            thread=chat_thread,
                            sender=applicant.user if applicant.user else None,
                            message=request.POST.get('cover_letter',
                                                     '') or "Здравствуйте! Я откликнулся на вашу вакансию."
                        )

                # Обновляем переменные для отображения
                has_applied = True
                show_chat_button = True
                messages.success(request, 'Ваш отклик успешно отправлен! Чат создан.')

        else:
            # Обработка для авторизованных пользователей
            if request.user.userprofile.role == 'applicant':
                try:
                    applicant = request.user.applicant

                    if not has_applied:
                        # Создаем отклик
                        application = Application.objects.create(
                            vacancy=vacancy,
                            applicant=applicant,
                            cover_letter=request.POST.get('cover_letter', '')
                        )

                        # Создаем чат сразу
                        if vacancy.company and vacancy.company.userprofile_set.filter(role='hr').exists():
                            hr_user = vacancy.company.userprofile_set.filter(role='hr').first().user
                            chat_thread, created = ChatThread.get_or_create_chat(
                                vacancy=vacancy,
                                applicant=applicant,
                                hr_user=hr_user
                            )
                            if created:
                                ChatMessage.objects.create(
                                    thread=chat_thread,
                                    sender=request.user,
                                    message=request.POST.get('cover_letter',
                                                             '') or "Здравствуйте! Я откликнулся на вашу вакансию."
                                )

                        # Обновляем переменные для отображения
                        has_applied = True
                        show_chat_button = True
                        messages.success(request, 'Ваш отклик успешно отправлен! Чат создан.')
                    else:
                        messages.info(request, 'Вы уже откликались на эту вакансию.')

                except Applicant.DoesNotExist:
                    messages.error(request, 'Пожалуйста, заполните ваш профиль соискателя.')
                    return redirect('create_applicant_profile')
            else:
                messages.error(request, 'Откликаться на вакансии могут только соискатели.')

    # Форма для неавторизованных пользователей
    applicant_form = ApplicantForm()

    context = {
        'vacancy': vacancy,
        'applicant_form': applicant_form,
        'has_applied': has_applied,
        'chat_thread': chat_thread,
        'show_chat_button': show_chat_button,
    }
    return render(request, 'career_app/vacancy_detail.html', context)


def internship_list(request):
    internships = Internship.objects.filter(status='published')

    query = request.GET.get('q')
    if query:
        internships = internships.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(specialty__icontains=query)
        )

    paginator = Paginator(internships, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'career_app/internship_list.html', context)


def internship_detail(request, pk):
    try:
        internship = get_object_or_404(Internship, pk=pk, status='published')
    except Internship.DoesNotExist:
        messages.error(request, 'Стажировка не найдена или еще не опубликована.')
        return redirect('vacancy_list')

    # Инициализируем переменные
    has_applied = False
    chat_thread = None
    applicant = None
    show_chat_button = False

    # Проверяем для авторизованных пользователей-соискателей
    if request.user.is_authenticated and hasattr(request.user,
                                                 'userprofile') and request.user.userprofile.role == 'applicant':
        try:
            applicant = request.user.applicant
            # Проверяем, откликался ли уже пользователь
            has_applied = InternshipResponse.objects.filter(
                internship=internship,
                applicant=applicant
            ).exists()

            # Ищем существующий чат
            if has_applied:
                chat_thread = ChatThread.objects.filter(
                    internship=internship,
                    applicant=applicant,
                    is_active=True
                ).first()
                if chat_thread:
                    show_chat_button = True

        except Applicant.DoesNotExist:
            pass

    # Обработка POST запроса (отклик)
    if request.method == 'POST' and internship.status == 'published':
        if request.user.is_authenticated and request.user.userprofile.role == 'applicant':
            try:
                applicant = request.user.applicant

                if not has_applied:
                    # Создаем отклик
                    response = InternshipResponse.objects.create(
                        internship=internship,
                        applicant=applicant,
                        cover_letter=request.POST.get('cover_letter', '')
                    )

                    # Создаем чат сразу
                    if internship.institution and internship.institution.userprofile_set.filter(
                            role='university').exists():
                        university_user = internship.institution.userprofile_set.filter(role='university').first().user
                        chat_thread, created = ChatThread.get_or_create_chat(
                            internship=internship,
                            applicant=applicant,
                            university_user=university_user
                        )
                        if created:
                            ChatMessage.objects.create(
                                thread=chat_thread,
                                sender=request.user,
                                message=request.POST.get('cover_letter',
                                                         '') or "Здравствуйте! Я откликнулся на вашу стажировку."
                            )

                    # Обновляем переменные для отображения
                    has_applied = True
                    show_chat_button = True
                    messages.success(request, 'Ваш отклик на стажировку успешно отправлен! Чат создан.')
                else:
                    messages.info(request, 'Вы уже откликались на эту стажировку.')

            except Applicant.DoesNotExist:
                messages.error(request, 'Пожалуйста, заполните ваш профиль соискателя.')
                return redirect('create_applicant_profile')
        else:
            messages.error(request, 'Для отклика на стажировку необходимо войти в систему как соискатель.')

    form = InternshipResponseForm()

    context = {
        'internship': internship,
        'form': form,
        'has_applied': has_applied,
        'chat_thread': chat_thread,
        'show_chat_button': show_chat_button,
        'applicant': applicant,
    }
    return render(request, 'career_app/internship_detail.html', context)

@login_required
def dashboard(request):
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.info(request, "Пожалуйста, завершите настройку вашего профиля.")
        return redirect('profile_setup')

    # Проверяем доступ к дашборду
    if not user_profile.can_access_dashboard():
        messages.warning(request, "Ваш аккаунт ожидает подтверждения администратором.")
        return redirect('pending_approval')

    if user_profile.role == 'admin':
        return admin_dashboard(request)
    elif user_profile.role == 'hr':
        return hr_dashboard(request)
    elif user_profile.role == 'university':
        return university_dashboard(request)
    else:
        return applicant_dashboard(request)


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Статистика для администратора
    vacancies_count = Vacancy.objects.count()
    published_vacancies = Vacancy.objects.filter(status='published').count()
    moderation_vacancies = Vacancy.objects.filter(status='moderation').count()

    internships_count = Internship.objects.count()
    published_internships = Internship.objects.filter(status='published').count()
    moderation_internships = Internship.objects.filter(status='moderation').count()

    applications_count = Application.objects.count()
    total_companies = Company.objects.count()

    context = {
        'vacancies_count': vacancies_count,
        'published_vacancies': published_vacancies,
        'moderation_vacancies': moderation_vacancies,
        'internships_count': internships_count,
        'published_internships': published_internships,
        'moderation_internships': moderation_internships,
        'applications_count': applications_count,
        'total_companies': total_companies,
    }
    return render(request, 'career_app/admin_dashboard.html', context)

@login_required
@user_passes_test(is_hr)
def hr_dashboard(request):
    company = request.user.userprofile.company
    vacancies = Vacancy.objects.filter(company=company)
    applications = Application.objects.filter(vacancy__company=company)

    # Статистика
    vacancies_published = vacancies.filter(status='published').count()
    vacancies_moderation = vacancies.filter(status='moderation').count()

    context = {
        'company': company,
        'vacancies': vacancies,
        'applications': applications,
        'vacancies_published': vacancies_published,
        'vacancies_moderation': vacancies_moderation,
    }
    return render(request, 'career_app/hr_dashboard.html', context)


@login_required
@user_passes_test(is_university)
def university_dashboard(request):
    institution = request.user.userprofile.institution
    internships = Internship.objects.filter(institution=institution)

    # Получаем отклики на стажировки
    internship_responses = InternshipResponse.objects.filter(
        internship__institution=institution
    ).select_related('applicant', 'internship').order_by('-applied_at')

    # Статистика
    internships_published = internships.filter(status='published').count()
    internships_moderation = internships.filter(status='moderation').count()
    total_responses = internship_responses.count()

    context = {
        'institution': institution,
        'internships': internships,
        'internship_responses': internship_responses,
        'internships_published': internships_published,
        'internships_moderation': internships_moderation,
        'total_responses': total_responses,
    }
    return render(request, 'career_app/university_dashboard.html', context)


@login_required
def applicant_dashboard(request):
    try:
        applicant = request.user.applicant
        applications = Application.objects.filter(applicant=applicant)
        internship_responses = InternshipResponse.objects.filter(applicant=applicant)
    except Applicant.DoesNotExist:
        applicant = None
        applications = []
        internship_responses = []

    context = {
        'applicant': applicant,
        'applications': applications,
        'internship_responses': internship_responses,
    }
    return render(request, 'career_app/applicant_dashboard.html', context)

@login_required
@user_passes_test(is_hr)
def create_vacancy(request):
    if request.method == 'POST':
        form = VacancyForm(request.POST)
        if form.is_valid():
            vacancy = form.save(commit=False)
            vacancy.company = request.user.userprofile.company
            vacancy.created_by = request.user
            vacancy.status = 'moderation'
            vacancy.save()
            messages.success(request, 'Вакансия отправлена на модерацию!')
            return redirect('hr_dashboard')  # Исправлено здесь
    else:
        form = VacancyForm()

    context = {'form': form}
    return render(request, 'career_app/vacancy_form.html', context)


@login_required
@user_passes_test(is_university)
def create_internship(request):
    if request.method == 'POST':
        form = InternshipForm(request.POST)
        if form.is_valid():
            internship = form.save(commit=False)
            internship.institution = request.user.userprofile.institution
            internship.created_by = request.user
            internship.status = 'moderation'
            internship.save()
            messages.success(request, 'Заявка на стажировку отправлена на модерацию!')
            return redirect('university_dashboard')  # Исправлено здесь
    else:
        form = InternshipForm()

    context = {'form': form}
    return render(request, 'career_app/internship_form.html', context)

@login_required
@user_passes_test(is_admin)
def moderation_list(request):
    vacancies = Vacancy.objects.filter(status='moderation')
    internships = Internship.objects.filter(status='moderation')

    context = {
        'vacancies': vacancies,
        'internships': internships,
    }
    return render(request, 'career_app/moderation_list.html', context)


@login_required
@user_passes_test(is_admin)
def moderate_vacancy(request, pk, action):
    vacancy = get_object_or_404(Vacancy, pk=pk)

    if action == 'approve':
        vacancy.status = 'published'
        vacancy.save()
        messages.success(request, f'Вакансия "{vacancy.title}" опубликована!')
    elif action == 'reject':
        vacancy.status = 'rejected'
        vacancy.save()
        messages.success(request, f'Вакансия "{vacancy.title}" отклонена!')

    return redirect('moderation_list')


@login_required
@user_passes_test(is_admin)
def moderate_internship(request, pk, action):
    internship = get_object_or_404(Internship, pk=pk)

    if action == 'approve':
        internship.status = 'published'
        internship.save()
        messages.success(request, f'Стажировка "{internship.title}" опубликована!')
    elif action == 'reject':
        internship.status = 'rejected'
        internship.save()
        messages.success(request, f'Стажировка "{internship.title}" отклонена!')

    return redirect('moderation_list')


def get_analytics_data(request):
    """Вспомогательная функция для получения данных аналитики"""
    # Параметры фильтрации
    period = request.GET.get('period', '30')
    category_id = request.GET.get('category', '')
    company_id = request.GET.get('company', '')
    status = request.GET.get('status', '')

    # Базовые queryset с фильтрами
    vacancy_filters = Q()
    application_filters = Q()
    internship_filters = Q()
    internship_response_filters = Q()

    # Период фильтрации
    if period != 'all':
        days = int(period)
        start_date = timezone.now() - timedelta(days=days)
        vacancy_filters &= Q(created_at__gte=start_date)
        application_filters &= Q(applied_at__gte=start_date)
        internship_filters &= Q(created_at__gte=start_date)
        internship_response_filters &= Q(applied_at__gte=start_date)

    if category_id:
        vacancy_filters &= Q(category_id=category_id)
        internship_filters &= Q(category_id=category_id)

    if company_id:
        vacancy_filters &= Q(company_id=company_id)

    if status:
        vacancy_filters &= Q(status=status)
        internship_filters &= Q(status=status)

    # Основная статистика
    vacancies = Vacancy.objects.filter(vacancy_filters)
    applications = Application.objects.filter(application_filters)
    internships = Internship.objects.filter(internship_filters)
    internship_responses = InternshipResponse.objects.filter(internship_response_filters)

    # Ключевые метрики
    total_vacancies = vacancies.count()
    total_applications = applications.count()
    total_companies = Company.objects.filter(is_approved=True).count()
    total_internships = internships.count()
    total_internship_responses = internship_responses.count()

    # Активные метрики
    active_vacancies = vacancies.filter(status='published').count()
    active_companies = Company.objects.filter(
        is_approved=True,
        vacancy__status='published'
    ).distinct().count()
    active_internships = internships.filter(status='published').count()

    # Новые отклики за последние 7 дней
    new_applications = Application.objects.filter(
        applied_at__gte=timezone.now() - timedelta(days=7)
    ).count()

    # Конверсия (отклики на вакансию)
    conversion_rate = 0
    if total_vacancies > 0:
        conversion_rate = round((total_applications / total_vacancies) * 100, 1)

    # Статистика по компаниям - ИСПРАВЛЕНО
    company_stats = Vacancy.objects.filter(vacancy_filters).values(
        'company__name', 'company_id'
    ).annotate(
        vacancy_count=Count('id'),
        application_count=Count('application'),
        published_vacancies=Count('id', filter=Q(status='published')),
        avg_salary=Avg('salary_amount')
    ).order_by('-application_count')[:10]

    # Рассчитываем conversion_rate и efficiency в Python
    for company in company_stats:
        vacancy_count = company['vacancy_count'] or 1  # Избегаем деления на ноль
        application_count = company['application_count'] or 0

        if vacancy_count > 0:
            company['conversion_rate'] = round((application_count / vacancy_count) * 100, 1)
        else:
            company['conversion_rate'] = 0

        if vacancy_count > 0 and application_count > 0:
            published_ratio = company['published_vacancies'] / vacancy_count
            conversion_ratio = application_count / vacancy_count
            efficiency = (conversion_ratio * published_ratio) * 100
            company['efficiency'] = min(efficiency, 100)
        else:
            company['efficiency'] = 0

    # Популярные вакансии - ИСПРАВЛЕНО
    popular_vacancies = Vacancy.objects.filter(vacancy_filters).annotate(
        application_count=Count('application'),
        view_count=Count('views', distinct=True)
    ).order_by('-application_count')[:10]

    # Рассчитываем CTR в Python
    for vacancy in popular_vacancies:
        view_count = vacancy.view_count or 1  # Избегаем деления на ноль
        if view_count > 0:
            vacancy.ctr = round((vacancy.application_count / view_count) * 100, 1)
        else:
            vacancy.ctr = 0

    # Статистика по времени - ИСПРАВЛЕНО
    timeline_labels = []
    timeline_vacancies = []
    timeline_applications = []

    if period != 'all':
        days = min(int(period), 90)

        if days <= 30:
            # Дневная статистика
            for i in range(days, -1, -1):
                day_start = timezone.now() - timedelta(days=i + 1)
                day_end = timezone.now() - timedelta(days=i)

                vac_count = Vacancy.objects.filter(
                    created_at__range=(day_start, day_end)
                ).count()
                app_count = Application.objects.filter(
                    applied_at__range=(day_start, day_end)
                ).count()

                timeline_vacancies.append(vac_count)
                timeline_applications.append(app_count)
                timeline_labels.append(day_end.strftime('%d.%m'))
        else:
            # Недельная статистика
            weeks = days // 7
            for i in range(weeks, -1, -1):
                week_start = timezone.now() - timedelta(weeks=i + 1)
                week_end = timezone.now() - timedelta(weeks=i)

                vac_count = Vacancy.objects.filter(
                    created_at__range=(week_start, week_end)
                ).count()
                app_count = Application.objects.filter(
                    applied_at__range=(week_start, week_end)
                ).count()

                timeline_vacancies.append(vac_count)
                timeline_applications.append(app_count)
                timeline_labels.append(f"{week_start.strftime('%d.%m')}-{week_end.strftime('%d.%m')}")
    else:
        # Для "все время" - группировка по месяцам
        months = 12
        for i in range(months, -1, -1):
            month_start = timezone.now() - timedelta(days=30 * (i + 1))
            month_end = timezone.now() - timedelta(days=30 * i)

            vac_count = Vacancy.objects.filter(
                created_at__range=(month_start, month_end)
            ).count()
            app_count = Application.objects.filter(
                applied_at__range=(month_start, month_end)
            ).count()

            timeline_vacancies.append(vac_count)
            timeline_applications.append(app_count)
            timeline_labels.append(month_end.strftime('%b %Y'))

    # Статистика по категориям - ИСПРАВЛЕНО
    category_stats = Vacancy.objects.filter(vacancy_filters).values(
        'category__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:8]

    # Если нет категорий, создаем демо-данные
    if not category_stats:
        category_stats = [
            {'category__name': 'IT', 'count': 15},
            {'category__name': 'Маркетинг', 'count': 12},
            {'category__name': 'Продажи', 'count': 8},
            {'category__name': 'Финансы', 'count': 6},
            {'category__name': 'HR', 'count': 4},
            {'category__name': 'Дизайн', 'count': 3},
        ]

    category_labels = [item['category__name'] or 'Без категории' for item in category_stats]
    category_data = [item['count'] for item in category_stats]

    # Статистика по статусам заявок - ИСПРАВЛЕНО
    application_status_stats = applications.values('status').annotate(
        count=Count('id')
    ).order_by('-count')

    # Если нет данных, создаем демо-данные
    if not application_status_stats:
        application_status_stats = [
            {'status': 'pending', 'count': 15},
            {'status': 'reviewed', 'count': 8},
            {'status': 'accepted', 'count': 3},
            {'status': 'rejected', 'count': 4}
        ]

    # Преобразуем статусы в читаемый формат
    status_display_map = {
        'pending': 'На рассмотрении',
        'reviewed': 'Просмотрено',
        'accepted': 'Принято',
        'rejected': 'Отклонено',
        'new': 'Новые'
    }

    status_labels = []
    status_data = []

    for stat in application_status_stats:
        status_key = stat['status']
        display_name = status_display_map.get(status_key, status_key)
        status_labels.append(display_name)
        status_data.append(stat['count'])

    # Географическая статистика
    location_stats = []
    if Vacancy.objects.filter(location__isnull=False).exists():
        location_data = Vacancy.objects.filter(
            vacancy_filters,
            location__isnull=False
        ).values('location').annotate(
            vacancy_count=Count('id'),
            avg_salary=Avg('salary_amount')
        ).order_by('-vacancy_count')[:10]

        total_location_vacancies = sum(item['vacancy_count'] for item in location_data)
        for location in location_data:
            if total_location_vacancies > 0:
                market_share = round((location['vacancy_count'] / total_location_vacancies) * 100, 1)
            else:
                market_share = 0

            location_stats.append({
                'location': location['location'],
                'vacancy_count': location['vacancy_count'],
                'avg_salary': location['avg_salary'] or 0,
                'market_share': market_share,
                'trend': 0,  # Упрощенная версия
                'conversion_rate': 0  # Упрощенная версия
            })

    # Статистика по стажировкам
    internship_applications = internship_responses.count()
    internship_conversion = 0
    if total_internships > 0:
        internship_conversion = round((internship_applications / total_internships) * 100, 1)

    # Рост (реальные данные)
    if period != 'all':
        days = int(period)
        previous_period_start = timezone.now() - timedelta(days=days * 2)
        previous_period_end = timezone.now() - timedelta(days=days)

        previous_period_vacancies = Vacancy.objects.filter(
            created_at__range=(previous_period_start, previous_period_end)
        ).count()

        previous_period_applications = Application.objects.filter(
            applied_at__range=(previous_period_start, previous_period_end)
        ).count()

        previous_period_companies = Company.objects.filter(
            is_approved=True,
            created_at__range=(previous_period_start, previous_period_end)
        ).count()
    else:
        previous_period_vacancies = 0
        previous_period_applications = 0
        previous_period_companies = 0

    # Расчет роста
    vacancy_growth = calculate_growth(total_vacancies, previous_period_vacancies)
    application_growth = calculate_growth(total_applications, previous_period_applications)
    company_growth = calculate_growth(total_companies, previous_period_companies)

    # Среднее время отклика
    avg_response_time = None
    if applications.exists():
        try:
            response_times = []
            for application in applications.select_related('vacancy')[:100]:
                if application.vacancy.created_at:
                    response_time = (application.applied_at - application.vacancy.created_at).total_seconds() / 3600
                    response_times.append(response_time)

            if response_times:
                avg_response_time = round(sum(response_times) / len(response_times), 1)
        except:
            avg_response_time = None

    return {
        # Основные метрики
        'total_vacancies': total_vacancies,
        'total_applications': total_applications,
        'total_companies': total_companies,
        'total_internships': total_internships,

        # Активные метрики
        'active_vacancies': active_vacancies,
        'active_companies': active_companies,
        'active_internships': active_internships,
        'new_applications': new_applications,

        # Процентные показатели
        'conversion_rate': conversion_rate,
        'vacancy_growth': vacancy_growth,
        'application_growth': application_growth,
        'company_growth': company_growth,

        # Детальная статистика
        'company_stats': list(company_stats),
        'popular_vacancies': list(popular_vacancies),
        'application_status_stats': list(application_status_stats),

        # Визуализации
        'timeline_labels': timeline_labels,
        'timeline_vacancies': timeline_vacancies,
        'timeline_applications': timeline_applications,
        'category_labels': category_labels,
        'category_data': category_data,
        'status_labels': status_labels,
        'status_data': status_data,

        # Дополнительная аналитика
        'location_stats': location_stats,
        'internship_applications': internship_applications,
        'internship_conversion': internship_conversion,
        'avg_response_time': avg_response_time,

        # Фильтры
        'period': period,
        'selected_category': category_id,
        'selected_company': company_id,
        'selected_status': status,
        'categories': Category.objects.all(),
        'companies': Company.objects.filter(is_approved=True),
    }

@login_required
@user_passes_test(is_admin)
def analytics(request):
    """Основная страница аналитики"""
    analytics_data = get_analytics_data(request)
    return render(request, 'career_app/analytics.html', analytics_data)


@login_required
@user_passes_test(is_admin)
def export_analytics(request, format_type):
    """Экспорт аналитики в Excel или PDF"""
    analytics_data = get_analytics_data(request)

    if format_type == 'excel':
        return export_analytics_to_excel(request, analytics_data)
    elif format_type == 'pdf':
        return export_analytics_to_pdf(request, analytics_data)
    else:
        messages.error(request, 'Неверный формат экспорта')
        return redirect('analytics')


def export_analytics_to_excel(request, analytics_data):
    """Экспорт аналитики в Excel"""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book

        # Лист с основной статистикой
        basic_stats = pd.DataFrame([
            ['Всего вакансий', analytics_data['total_vacancies']],
            ['Активных вакансий', analytics_data['active_vacancies']],
            ['Всего откликов', analytics_data['total_applications']],
            ['Новых откликов', analytics_data['new_applications']],
            ['Всего компаний', analytics_data['total_companies']],
            ['Активных компаний', analytics_data['active_companies']],
            ['Всего стажировок', analytics_data['total_internships']],
            ['Откликов на стажировки', analytics_data['internship_applications']],
            ['Конверсия', f"{analytics_data['conversion_rate']}%"],
            ['Рост вакансий', f"{analytics_data['vacancy_growth']}%"],
            ['Рост откликов', f"{analytics_data['application_growth']}%"],
            ['Рост компаний', f"{analytics_data['company_growth']}%"],
        ], columns=['Показатель', 'Значение'])

        basic_stats.to_excel(writer, sheet_name='Основная статистика', index=False)

        # Лист со статистикой по компаниям
        if analytics_data['company_stats']:
            company_data = []
            for company in analytics_data['company_stats']:
                company_data.append([
                    company.get('company__name', 'Не указана'),
                    company.get('vacancy_count', 0),
                    company.get('application_count', 0),
                    company.get('published_vacancies', 0),
                    f"{company.get('conversion_rate', 0):.1f}%",
                    f"{company.get('efficiency', 0):.1f}%",
                    f"{company.get('avg_salary', 0):.0f} ₽" if company.get('avg_salary') else 'Не указана'
                ])

            company_df = pd.DataFrame(company_data,
                                      columns=['Компания', 'Всего вакансий', 'Отклики', 'Опубликовано', 'Конверсия',
                                               'Эффективность', 'Ср. зарплата'])
            company_df.to_excel(writer, sheet_name='Статистика по компаниям', index=False)

        # Лист с популярными вакансиями
        if analytics_data['popular_vacancies']:
            vacancy_data = []
            for vacancy in analytics_data['popular_vacancies']:
                vacancy_data.append([
                    vacancy.title[:50],
                    vacancy.company.name if vacancy.company else 'Не указана',
                    getattr(vacancy, 'application_count', 0),
                    getattr(vacancy, 'view_count', 0),
                    f"{getattr(vacancy, 'ctr', 0):.1f}%",
                    vacancy.status
                ])

            vacancy_df = pd.DataFrame(vacancy_data,
                                      columns=['Вакансия', 'Компания', 'Отклики', 'Просмотры', 'CTR', 'Статус'])
            vacancy_df.to_excel(writer, sheet_name='Популярные вакансии', index=False)

        # Лист со статусами откликов
        status_data = []
        for i, status in enumerate(analytics_data['status_labels']):
            status_data.append([
                status,
                analytics_data['status_data'][i]
            ])

        status_df = pd.DataFrame(status_data, columns=['Статус', 'Количество'])
        status_df.to_excel(writer, sheet_name='Статусы откликов', index=False)

    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response[
        'Content-Disposition'] = f'attachment; filename=analytics_{datetime.datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'

    return response


def export_analytics_to_pdf(request, analytics_data):
    """Экспорт аналитики в PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    elements = []
    styles = getSampleStyleSheet()

    # Стиль для заголовка
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # CENTER
    )

    # Заголовок
    title = Paragraph(f"Аналитика системы карьерного портала", title_style)
    elements.append(title)

    subtitle = Paragraph(f"Отчет сгенерирован: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal'])
    elements.append(subtitle)
    elements.append(Spacer(1, 20))

    # Основная статистика
    elements.append(Paragraph("Основные метрики:", styles['Heading2']))

    basic_data = [
        ['Показатель', 'Значение'],
        ['Всего вакансий', str(analytics_data['total_vacancies'])],
        ['Активных вакансий', str(analytics_data['active_vacancies'])],
        ['Всего откликов', str(analytics_data['total_applications'])],
        ['Новых откликов', str(analytics_data['new_applications'])],
        ['Всего компаний', str(analytics_data['total_companies'])],
        ['Конверсия', f"{analytics_data['conversion_rate']}%"],
        ['Рост вакансий', f"{analytics_data['vacancy_growth']}%"],
    ]

    table = Table(basic_data, colWidths=[3 * inch, 2 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Статистика по компаниям
    if analytics_data['company_stats']:
        elements.append(Paragraph("Топ компаний по откликам:", styles['Heading2']))

        company_data = [['Компания', 'Вакансии', 'Отклики', 'Конверсия']]
        for company in analytics_data['company_stats'][:5]:
            company_data.append([
                company.get('company__name', 'Не указана')[:25],
                str(company.get('vacancy_count', 0)),
                str(company.get('application_count', 0)),
                f"{company.get('conversion_rate', 0):.1f}%"
            ])

        company_table = Table(company_data, colWidths=[2.5 * inch, 1 * inch, 1 * inch, 1 * inch])
        company_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(company_table)
        elements.append(Spacer(1, 20))

    # Статусы откликов
    elements.append(Paragraph("Статусы откликов:", styles['Heading2']))

    status_data = [['Статус', 'Количество']]
    for i, status_label in enumerate(analytics_data['status_labels']):
        status_data.append([
            status_label,
            str(analytics_data['status_data'][i])
        ])

    status_table = Table(status_data, colWidths=[3 * inch, 2 * inch])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(status_table)

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response[
        'Content-Disposition'] = f'attachment; filename=analytics_{datetime.datetime.now().strftime("%Y%m%d_%H%M")}.pdf'

    return response





def calculate_growth(current, previous):
    """Вспомогательная функция для расчета роста"""
    if previous == 0:
        return 100 if current > 0 else 0
    growth = ((current - previous) / previous) * 100
    return round(growth, 1)

@login_required
def create_applicant_profile(request):
    """Перенаправляем на общую настройку профиля"""
    # Устанавливаем роль соискателя если еще не установлена
    try:
        user_profile = request.user.userprofile
        if user_profile.role != 'applicant':
            user_profile.role = 'applicant'
            user_profile.save()
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user, role='applicant')

    return redirect('profile_setup')


@login_required
def update_applicant_profile(request):
    """Перенаправляем на общую настройку профиля"""
    return redirect('profile_setup')


@login_required
def profile_setup(request):
    """Универсальная настройка профиля"""
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user, role='applicant')

    # Если пользователь - соискатель, получаем или создаем его профиль
    applicant = None
    if user_profile.role == 'applicant':
        try:
            applicant = request.user.applicant
        except Applicant.DoesNotExist:
            applicant = Applicant.objects.create(
                user=request.user,
                first_name=request.user.first_name or '',
                last_name=request.user.last_name or '',
                email=request.user.email or ''
            )

    if request.method == 'POST':
        user_profile_form = UserProfileForm(request.POST, instance=user_profile)

        # Для соискателя также обрабатываем форму Applicant
        if user_profile.role == 'applicant':
            applicant_form = ApplicantForm(request.POST, request.FILES, instance=applicant)
            if user_profile_form.is_valid() and applicant_form.is_valid():
                user_profile_form.save()
                applicant_form.save()
                messages.success(request, 'Профиль успешно обновлен!')
                return redirect('dashboard')
        else:
            if user_profile_form.is_valid():
                user_profile_form.save()
                messages.success(request, 'Профиль успешно обновлен!')
                return redirect('dashboard')
    else:
        user_profile_form = UserProfileForm(instance=user_profile)
        applicant_form = ApplicantForm(instance=applicant) if user_profile.role == 'applicant' else None

    context = {
        'user_profile_form': user_profile_form,
        'applicant_form': applicant_form,
    }
    return render(request, 'career_app/profile_setup.html', context)


def role_selection(request):
    """Первая страница - выбор роли для входа"""
    if request.method == 'POST':
        form = RoleSelectionForm(request.POST)
        if form.is_valid():
            request.session['selected_role'] = form.cleaned_data['role']
            return redirect('custom_login')
    else:
        form = RoleSelectionForm()

    context = {
        'form': form,
        'role_choices': [
            ('applicant', 'Соискатель'),
            ('hr', 'HR компании'),
            ('university', 'Представитель вуза'),
            ('admin', 'Администратор ОЭЗ'),
        ]
    }
    return render(request, 'career_app/role_selection.html', context)


def custom_login(request):
    """Вторая страница - ввод логина и пароля"""
    selected_role = request.session.get('selected_role')

    if not selected_role:
        return redirect('role_selection')

    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                try:
                    user_profile = user.userprofile
                    if user_profile.role != selected_role:
                        messages.error(request,
                                       f'Выбранная роль не соответствует вашему профилю. Ваша роль: {user_profile.get_role_display()}')
                        return redirect('role_selection')

                    # Для HR и университетов проверяем подтверждение
                    if user_profile.role in ['hr', 'university'] and not user_profile.is_approved:
                        messages.warning(request, 'Ваш аккаунт ожидает подтверждения администратором.')
                        return redirect('pending_approval')

                    login(request, user)
                    return redirect('dashboard')

                except UserProfile.DoesNotExist:
                    messages.error(request, 'Профиль пользователя не найден.')
                    return redirect('role_selection')
            else:
                messages.error(request, 'Неверный логин или пароль.')
    else:
        form = CustomLoginForm()

    role_display = dict(RoleSelectionForm.ROLE_CHOICES).get(selected_role, selected_role)

    context = {
        'form': form,
        'selected_role': selected_role,
        'role_display': role_display,
    }
    return render(request, 'career_app/custom_login.html', context)

def pending_approval(request):
    """Страница ожидания подтверждения"""
    return render(request, 'career_app/pending_approval.html')

@login_required
@user_passes_test(is_admin)
def admin_promotion(request):
    """Назначение новых администраторов"""
    if request.method == 'POST':
        form = AdminPromotionForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']

            try:
                user_profile = user.userprofile
                # Меняем роль на админа
                user_profile.role = 'admin'
                user_profile.is_approved = True  # Админы автоматически подтверждаются
                user_profile.save()

                messages.success(request, f'Пользователь {user.username} теперь администратор!')
                return redirect('admin_promotion')

            except UserProfile.DoesNotExist:
                # Создаем новый профиль с ролью админа
                UserProfile.objects.create(
                    user=user,
                    role='admin',
                    is_approved=True
                )
                messages.success(request, f'Пользователь {user.username} теперь администратор!')
                return redirect('admin_promotion')
    else:
        form = AdminPromotionForm()

    # Список текущих администраторов
    current_admins = UserProfile.objects.filter(role='admin').select_related('user')

    context = {
        'form': form,
        'current_admins': current_admins,
    }
    return render(request, 'career_app/admin_promotion.html', context)


@login_required
@user_passes_test(is_admin)
def revoke_admin(request, user_id):
    """Отзыв прав администратора"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)

        # Не позволяем отозвать права у самого себя
        if user == request.user:
            messages.error(request, 'Вы не можете отозвать права администратора у самого себя!')
            return redirect('admin_promotion')

        try:
            user_profile = user.userprofile
            # Меняем роль на соискателя (или другую базовую роль)
            user_profile.role = 'applicant'
            user_profile.save()

            messages.success(request, f'Права администратора отозваны у пользователя {user.username}')
        except UserProfile.DoesNotExist:
            messages.error(request, 'Профиль пользователя не найден')

    return redirect('admin_promotion')


@login_required
@user_passes_test(is_admin)
def role_approval_list(request):
    """Список запросов на подтверждение ролей HR и университетов"""
    pending_requests = RoleApprovalRequest.objects.filter(status='pending').select_related('user')
    approved_requests = RoleApprovalRequest.objects.filter(status='approved').select_related('user')[
                        :10]  # Последние 10
    rejected_requests = RoleApprovalRequest.objects.filter(status='rejected').select_related('user')[
                        :10]  # Последние 10

    context = {
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
    }
    return render(request, 'career_app/role_approval_list.html', context)


@login_required
@user_passes_test(is_admin)
def approve_role(request, request_id, action):
    """Подтверждение или отклонение роли"""
    role_request = get_object_or_404(RoleApprovalRequest, id=request_id)

    if action == 'approve':
        role_request.status = 'approved'
        role_request.reviewed_at = timezone.now()
        role_request.reviewed_by = request.user

        # Обновляем профиль пользователя
        user_profile = role_request.user.userprofile
        user_profile.is_approved = True
        user_profile.save()

        # Подтверждаем компанию или учебное заведение
        if role_request.requested_role == 'hr' and user_profile.company:
            user_profile.company.is_approved = True
            user_profile.company.save()
        elif role_request.requested_role == 'university' and user_profile.institution:
            user_profile.institution.is_approved = True
            user_profile.institution.save()

        messages.success(request, f'Роль для пользователя {role_request.user.username} подтверждена!')

    elif action == 'reject':
        role_request.status = 'rejected'
        role_request.reviewed_at = timezone.now()
        role_request.reviewed_by = request.user

        # Можно также отправить уведомление пользователю
        messages.success(request, f'Запрос роли для пользователя {role_request.user.username} отклонен!')

    role_request.save()
    return redirect('role_approval_list')


# views.py - добавить новые представления
@login_required
def chat_list(request):
    """Список чатов пользователя"""
    user_profile = request.user.userprofile

    if user_profile.role == 'applicant':
        # Для соискателя - чаты с HR и университетами
        threads = ChatThread.objects.filter(
            applicant__user=request.user,
            is_active=True
        ).select_related('vacancy', 'internship', 'hr_user', 'university_user')

    elif user_profile.role == 'hr':
        # Для HR - чаты по вакансиям его компании
        threads = ChatThread.objects.filter(
            vacancy__company=user_profile.company,
            is_active=True
        ).select_related('vacancy', 'applicant', 'hr_user')

    elif user_profile.role == 'university':
        # Для университета - чаты по стажировкам его учреждения
        threads = ChatThread.objects.filter(
            internship__institution=user_profile.institution,
            is_active=True
        ).select_related('internship', 'applicant', 'university_user')

    else:
        threads = ChatThread.objects.none()

    # Помечаем непрочитанные сообщения
    for thread in threads:
        thread.unread_count = thread.messages.filter(
            is_read=False
        ).exclude(sender=request.user).count()

    context = {
        'threads': threads,
    }
    return render(request, 'career_app/chat_list.html', context)


@login_required
def chat_detail(request, thread_id):
    """Детальная страница чата"""
    thread = get_object_or_404(ChatThread, id=thread_id)

    # Проверка прав доступа к чату
    user_profile = request.user.userprofile
    has_access = False

    if user_profile.role == 'applicant':
        has_access = thread.applicant.user == request.user
    elif user_profile.role == 'hr':
        has_access = thread.vacancy and thread.vacancy.company == user_profile.company
    elif user_profile.role == 'university':
        has_access = thread.internship and thread.internship.institution == user_profile.institution
    elif user_profile.role == 'admin':
        has_access = True

    if not has_access:
        messages.error(request, 'У вас нет доступа к этому чату.')
        return redirect('chat_list')

    # Помечаем сообщения как прочитанные
    thread.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    if request.method == 'POST':
        form = ChatMessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.thread = thread
            message.sender = request.user
            message.save()

            # Обновляем время последней активности чата
            thread.save()

            return redirect('chat_detail', thread_id=thread_id)
    else:
        form = ChatMessageForm()

    messages_list = thread.messages.all().select_related('sender')

    context = {
        'thread': thread,
        'messages_list': messages_list,
        'form': form,
        'other_user': thread.get_other_participant(request.user),
    }
    return render(request, 'career_app/chat_detail.html', context)


@login_required
def create_chat_from_application(request, application_id):
    """Создание чата из отклика на вакансию"""
    application = get_object_or_404(Application, id=application_id)

    # Проверяем, что пользователь - HR компании вакансии
    if not (request.user.userprofile.role == 'hr' and
            application.vacancy.company == request.user.userprofile.company):
        messages.error(request, 'У вас нет прав для создания чата.')
        return redirect('hr_dashboard')

    # Создаем или получаем существующий чат
    thread, created = ChatThread.objects.get_or_create(
        vacancy=application.vacancy,
        applicant=application.applicant,
        hr_user=request.user,
        defaults={'is_active': True}
    )

    if created:
        # Создаем первое сообщение от HR
        ChatMessage.objects.create(
            thread=thread,
            sender=request.user,
            message=f"Здравствуйте! Благодарим за отклик на вакансию '{application.vacancy.title}'. Давайте обсудим вашу кандидатуру."
        )
        messages.success(request, 'Чат создан!')

    return redirect('chat_detail', thread_id=thread.id)


def terms_of_use(request):
    return render(request, 'career_app/terms_of_use.html')

def privacy_policy(request):
    return render(request, 'career_app/privacy_policy.html')

@login_required
def create_chat_from_internship_response(request, response_id):
    """Создание чата из отклика на стажировку"""
    response = get_object_or_404(InternshipResponse, id=response_id)

    # Проверяем, что пользователь - представитель университета
    if not (request.user.userprofile.role == 'university' and
            response.internship.institution == request.user.userprofile.institution):
        messages.error(request, 'У вас нет прав для создания чата.')
        return redirect('university_dashboard')

    # Создаем или получаем существующий чат
    thread, created = ChatThread.objects.get_or_create(
        internship=response.internship,
        applicant=response.applicant,
        university_user=request.user,
        defaults={'is_active': True}
    )

    if created:
        # Создаем первое сообщение от университета
        ChatMessage.objects.create(
            thread=thread,
            sender=request.user,
            message=f"Здравствуйте! Благодарим за интерес к стажировке '{response.internship.title}'. Давайте обсудим детали."
        )
        messages.success(request, 'Чат создан!')

    return redirect('chat_detail', thread_id=thread.id)


# Добавить в views.py

from .ai_matcher import AIMatcher
from .forms import IdealCandidateProfileForm, IdealVacancyProfileForm


@login_required
@user_passes_test(is_hr)
def create_ideal_candidate_profile(request):
    """Создание идеального профиля кандидата для HR"""
    if request.method == 'POST':
        form = IdealCandidateProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.hr_user = request.user
            profile.save()

            # Запускаем поиск кандидатов
            matches = AIMatcher.find_candidates_for_hr(profile)

            messages.success(request, f'Найдено {len(matches)} подходящих кандидатов!')
            return redirect('ai_candidate_results', profile_id=profile.id)
    else:
        form = IdealCandidateProfileForm()

    context = {
        'form': form,
        'editing': False,
    }
    return render(request, 'career_app/ideal_candidate_profile_form.html', context)


@login_required
def create_ideal_vacancy_profile(request):
    """Создание нового идеального профиля вакансии для соискателя"""
    try:
        applicant = request.user.applicant
    except Applicant.DoesNotExist:
        messages.error(request, 'Пожалуйста, заполните ваш профиль соискателя.')
        return redirect('create_applicant_profile')

    if request.method == 'POST':
        form = IdealVacancyProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.applicant = applicant
            profile.save()
            form.save_m2m()

            messages.success(request, 'Профиль создан! Теперь вы можете запустить поиск.')
            return redirect('ai_search_dashboard')
    else:
        form = IdealVacancyProfileForm()

    context = {
        'form': form,
        'editing': False,
    }
    return render(request, 'career_app/ideal_vacancy_profile_form.html', context)


@login_required
def edit_ideal_vacancy_profile(request, profile_id):
    """Редактирование существующего идеального профиля вакансии"""
    try:
        applicant = request.user.applicant
        profile = IdealVacancyProfile.objects.get(id=profile_id, applicant=applicant)
    except Applicant.DoesNotExist:
        messages.error(request, 'Пожалуйста, заполните ваш профиль соискателя.')
        return redirect('create_applicant_profile')
    except IdealVacancyProfile.DoesNotExist:
        messages.error(request, 'Профиль не найден или у вас нет прав для его редактирования.')
        return redirect('ai_search_dashboard')

    if request.method == 'POST':
        form = IdealVacancyProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('ai_search_dashboard')
    else:
        form = IdealVacancyProfileForm(instance=profile)

    context = {
        'form': form,
        'editing': True,
        'profile': profile,
    }
    return render(request, 'career_app/ideal_vacancy_profile_form.html', context)


@login_required
def ai_search_results(request, profile_id):
    """Результаты ИИ-поиска"""
    user_profile = request.user.userprofile

    try:
        if user_profile.role == 'hr':
            profile = IdealCandidateProfile.objects.get(id=profile_id, hr_user=request.user)
            matches = AISearchMatch.objects.filter(
                ideal_candidate_profile=profile
            ).select_related('matched_applicant').order_by('-match_percentage')
            template = 'career_app/ai_candidate_results.html'
        else:
            profile = IdealVacancyProfile.objects.get(id=profile_id, applicant__user=request.user)
            matches = AISearchMatch.objects.filter(
                ideal_vacancy_profile=profile
            ).select_related('matched_vacancy', 'matched_vacancy__company').order_by('-match_percentage')
            template = 'career_app/ai_vacancy_results.html'

        # ДИАГНОСТИКА: выводим отладочную информацию
        print(f"=== ДИАГНОСТИКА РЕЗУЛЬТАТОВ ===")
        print(f"Профиль: {profile.title}")
        print(f"Найдено совпадений в базе: {matches.count()}")
        for match in matches:
            if hasattr(match, 'matched_vacancy') and match.matched_vacancy:
                print(f"- Вакансия: {match.matched_vacancy.title} - {match.match_percentage}%")
            elif hasattr(match, 'matched_applicant') and match.matched_applicant:
                print(
                    f"- Кандидат: {match.matched_applicant.first_name} {match.matched_applicant.last_name} - {match.match_percentage}%")

        context = {
            'profile': profile,
            'matches': matches,
            'debug_info': {
                'matches_count': matches.count(),
                'profile_title': profile.title
            }
        }
        return render(request, template, context)

    except IdealCandidateProfile.DoesNotExist:
        messages.error(request, 'Профиль кандидата не найден.')
        return redirect('ai_search_dashboard')
    except IdealVacancyProfile.DoesNotExist:
        messages.error(request, 'Профиль вакансии не найден.')
        return redirect('ai_search_dashboard')

@login_required
@user_passes_test(is_hr)
def send_offer_to_candidate(request, match_id):
    """Отправка офера кандидату"""
    match = get_object_or_404(AISearchMatch, id=match_id, ideal_candidate_profile__hr_user=request.user)

    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()

        if not message_text:
            messages.error(request, 'Пожалуйста, напишите сообщение для кандидата.')
            return redirect('send_offer_to_candidate', match_id=match_id)

        try:
            # Создаем чат с кандидатом
            thread, created = ChatThread.get_or_create_chat(
                vacancy=None,  # Можно привязать к конкретной вакансии позже
                applicant=match.matched_applicant,
                hr_user=request.user
            )

            if thread:
                # Отправляем сообщение с офером
                offer_message = f"""🎯 Предложение от {request.user.userprofile.company.name}

{message_text}

Мы нашли вашу кандидатуру через ИИ-поиск - совпадение составило {match.match_percentage}%!

Готовы обсудить детали?"""

                chat_message = ChatMessage.objects.create(
                    thread=thread,
                    sender=request.user,
                    message=offer_message
                )

                match.status = 'offer_sent'
                match.save()

                messages.success(request, 'Предложение отправлено кандидату!')
                return redirect('chat_detail', thread_id=thread.id)
            else:
                messages.error(request, 'Не удалось создать чат с кандидатом.')

        except Exception as e:
            messages.error(request, f'Произошла ошибка при отправке предложения: {str(e)}')

    context = {'match': match}
    return render(request, 'career_app/send_offer.html', context)


@login_required
def ai_search_dashboard(request):
    """Дашборд ИИ-поиска"""
    user_profile = request.user.userprofile

    if user_profile.role == 'hr':
        profiles = IdealCandidateProfile.objects.filter(hr_user=request.user)
        recent_matches = AISearchMatch.objects.filter(
            ideal_candidate_profile__hr_user=request.user
        ).select_related('matched_applicant')[:5]
    elif user_profile.role == 'applicant':
        try:
            applicant = request.user.applicant
            profiles = IdealVacancyProfile.objects.filter(applicant=applicant)
            recent_matches = AISearchMatch.objects.filter(
                ideal_vacancy_profile__applicant=applicant
            ).select_related('matched_vacancy', 'matched_vacancy__company')[:5]
        except Applicant.DoesNotExist:
            profiles = []
            recent_matches = []
    else:
        profiles = []
        recent_matches = []

    context = {
        'profiles': profiles,
        'recent_matches': recent_matches,
    }
    return render(request, 'career_app/ai_search_dashboard.html', context)


# Добавить в конец views.py

@login_required
def create_or_edit_resume(request):
    """Создание или редактирование резюме"""
    try:
        applicant = request.user.applicant
    except Applicant.DoesNotExist:
        # Создаем нового соискателя
        applicant = Applicant.objects.create(
            user=request.user,
            first_name=request.user.first_name or '',
            last_name=request.user.last_name or '',
            email=request.user.email or ''
        )

    if request.method == 'POST':
        form = ApplicantResumeForm(request.POST, request.FILES, instance=applicant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Резюме успешно сохранено!')
            return redirect('applicant_dashboard')
    else:
        form = ApplicantResumeForm(instance=applicant)

    context = {'form': form}
    return render(request, 'career_app/applicant_resume_form.html', context)


@login_required
def applicant_resume_view(request, applicant_id=None):
    """Просмотр резюме"""
    if applicant_id:
        # Просмотр чужого резюме (для HR)
        applicant = get_object_or_404(Applicant, id=applicant_id, is_published=True)
    else:
        # Просмотр своего резюме
        try:
            applicant = request.user.applicant
        except Applicant.DoesNotExist:
            messages.error(request, 'Сначала создайте резюме')
            return redirect('create_or_edit_resume')

    context = {'applicant': applicant}
    return render(request, 'career_app/applicant_resume_view.html', context)


@login_required
@user_passes_test(is_hr)
def send_offer_to_candidate(request, match_id):
    """Отправка офера кандидату"""
    match = get_object_or_404(AISearchMatch, id=match_id, ideal_candidate_profile__hr_user=request.user)

    if request.method == 'POST':
        message_text = request.POST.get('message', '')

        # Создаем чат с кандидатом
        thread, created = ChatThread.get_or_create_chat(
            vacancy=None,  # Можно привязать к конкретной вакансии позже
            applicant=match.matched_applicant,
            hr_user=request.user
        )

        if created or thread:
            # Отправляем сообщение с офером
            offer_message = f"""🎯 Предложение от {request.user.userprofile.company.name}

По результатам ИИ-поиска ваша кандидатура подходит нам на {match.match_percentage}%!

{match.match_details.get('matched_skills', [])}

{message_text}

Готовы обсудить детали?"""

            ChatMessage.objects.create(
                thread=thread,
                sender=request.user,
                message=offer_message
            )

            match.status = 'offer_sent'
            match.save()

            messages.success(request, 'Предложение отправлено кандидату!')
            return redirect('chat_detail', thread_id=thread.id)

    context = {'match': match}
    return render(request, 'career_app/send_offer.html', context)


@login_required
def ai_search_dashboard(request):
    """Дашборд ИИ-поиска"""
    user_profile = request.user.userprofile

    if user_profile.role == 'hr':
        profiles = IdealCandidateProfile.objects.filter(hr_user=request.user)
        recent_matches = AISearchMatch.objects.filter(
            ideal_candidate_profile__hr_user=request.user
        ).select_related('matched_applicant')[:5]
        total_applicants = Applicant.objects.filter(is_published=True).count()
        context = {
            'profiles': profiles,
            'recent_matches': recent_matches,
            'total_applicants': total_applicants,
        }
    elif user_profile.role == 'applicant':
        try:
            applicant = request.user.applicant
            profiles = IdealVacancyProfile.objects.filter(applicant=applicant)
            recent_matches = AISearchMatch.objects.filter(
                ideal_vacancy_profile__applicant=applicant
            ).select_related('matched_vacancy', 'matched_vacancy__company')[:5]
            total_vacancies = Vacancy.objects.filter(status='published').count()
            context = {
                'profiles': profiles,
                'recent_matches': recent_matches,
                'total_vacancies': total_vacancies,
            }
        except Applicant.DoesNotExist:
            profiles = []
            recent_matches = []
            context = {
                'profiles': profiles,
                'recent_matches': recent_matches,
            }
    else:
        profiles = []
        recent_matches = []
        context = {
            'profiles': profiles,
            'recent_matches': recent_matches,
        }

    return render(request, 'career_app/ai_search_dashboard.html', context)

def applicant_resume(request):
    try:
        applicant = Applicant.objects.get(user=request.user)
    except Applicant.DoesNotExist:
        applicant = None

    if request.method == 'POST':
        form = ApplicantResumeForm(request.POST, request.FILES, instance=applicant, user=request.user)
        if form.is_valid():
            applicant = form.save(commit=False)
            applicant.user = request.user
            applicant.save()
            messages.success(request, 'Резюме успешно сохранено!')
            return redirect('applicant_dashboard')
    else:
        form = ApplicantResumeForm(instance=applicant, user=request.user)

    return render(request, 'applicant_rezume_form.html', {'form': form})


from django.http import JsonResponse
from .ai_matcher import AIMatcher
from .models import IdealVacancyProfile, Vacancy


@login_required
def force_ai_search(request, profile_id):
    """Принудительный запуск ИИ-поиска"""
    try:
        profile = IdealVacancyProfile.objects.get(id=profile_id, applicant__user=request.user)
        from .ai_matcher import AIMatcher

        # Запускаем поиск
        results = AIMatcher.find_vacancies_for_applicant(profile)

        # Проверяем сохраненные результаты
        saved_matches = AISearchMatch.objects.filter(ideal_vacancy_profile=profile)

        messages.success(request,
                         f'Поиск выполнен! Найдено {len(results)} вакансий, сохранено {saved_matches.count()} совпадений.')
        return redirect('ai_search_results', profile_id=profile_id)

    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('ai_search_dashboard')


@login_required
def run_ai_search(request, profile_id):
    """Запуск ИИ-поиска и отображение результатов"""
    try:
        user_profile = request.user.userprofile

        if user_profile.role == 'hr':
            profile = IdealCandidateProfile.objects.get(id=profile_id, hr_user=request.user)
            from .ai_matcher import AIMatcher
            results = AIMatcher.find_candidates_for_hr(profile)
            messages.success(request, f'Поиск завершен! Найдено {len(results)} кандидатов.')

        elif user_profile.role == 'applicant':
            profile = IdealVacancyProfile.objects.get(id=profile_id, applicant__user=request.user)
            from .ai_matcher import AIMatcher
            results = AIMatcher.find_vacancies_for_applicant(profile)
            messages.success(request, f'Поиск завершен! Найдено {len(results)} вакансий.')

        return redirect('ai_search_results', profile_id=profile_id)

    except Exception as e:
        messages.error(request, f'Ошибка при поиске: {str(e)}')
        return redirect('ai_search_dashboard')

@login_required
@user_passes_test(is_hr)
def edit_ideal_candidate_profile(request, profile_id):
    """Редактирование идеального профиля кандидата для HR"""
    try:
        profile = IdealCandidateProfile.objects.get(id=profile_id, hr_user=request.user)
    except IdealCandidateProfile.DoesNotExist:
        messages.error(request, 'Профиль не найден или у вас нет прав для его редактирования.')
        return redirect('ai_search_dashboard')

    if request.method == 'POST':
        form = IdealCandidateProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль кандидата успешно обновлен!')
            return redirect('ai_search_dashboard')
    else:
        form = IdealCandidateProfileForm(instance=profile)

    context = {
        'form': form,
        'editing': True,
        'profile': profile,
    }
    return render(request, 'career_app/ideal_candidate_profile_form.html', context)


@login_required
def ai_candidate_results(request, profile_id):
    """Результаты поиска кандидатов для HR"""
    try:
        profile = IdealCandidateProfile.objects.get(id=profile_id, hr_user=request.user)
        matches = AISearchMatch.objects.filter(
            ideal_candidate_profile=profile
        ).select_related('matched_applicant').order_by('-match_percentage')

        context = {
            'profile': profile,
            'matches': matches,
        }
        return render(request, 'career_app/ai_candidate_results.html', context)

    except IdealCandidateProfile.DoesNotExist:
        messages.error(request, 'Профиль кандидата не найден.')
        return redirect('ai_search_dashboard')


@login_required
def ai_vacancy_results(request, profile_id):
    """Результаты поиска вакансий для соискателей"""
    try:
        applicant = request.user.applicant
        profile = IdealVacancyProfile.objects.get(id=profile_id, applicant=applicant)
        matches = AISearchMatch.objects.filter(
            ideal_vacancy_profile=profile
        ).select_related('matched_vacancy', 'matched_vacancy__company').order_by('-match_percentage')

        context = {
            'profile': profile,
            'matches': matches,
        }
        return render(request, 'career_app/ai_vacancy_results.html', context)

    except IdealVacancyProfile.DoesNotExist:
        messages.error(request, 'Профиль вакансии не найден.')
        return redirect('ai_search_dashboard')
    except Applicant.DoesNotExist:
        messages.error(request, 'Профиль соискателя не найден.')
        return redirect('ai_search_dashboard')