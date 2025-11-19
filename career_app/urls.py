from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Основные URLs
    path('', views.home, name='home'),
    path('terms/', views.terms_of_use, name='terms_of_use'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('role_selection/', views.role_selection, name='role_selection'),
    path('login/', views.custom_login, name='custom_login'),
    path('register/', views.register, name='register'),
    path('pending-approval/', views.pending_approval, name='pending_approval'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # Админские URLs
    path('moderation/role-approval/', views.role_approval_list, name='role_approval_list'),
    path('moderation/role-approval/<int:request_id>/<str:action>/', views.approve_role, name='approve_role'),
    path('moderation/admin-promotion/', views.admin_promotion, name='admin_promotion'),
    path('moderation/revoke-admin/<int:user_id>/', views.revoke_admin, name='revoke_admin'),

    # Дашборды
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/hr/', views.hr_dashboard, name='hr_dashboard'),
    path('dashboard/university/', views.university_dashboard, name='university_dashboard'),
    path('dashboard/applicant/', views.applicant_dashboard, name='applicant_dashboard'),

    # Вакансии
    path('vacancies/', views.vacancy_list, name='vacancy_list'),
    path('vacancies/<int:pk>/', views.vacancy_detail, name='vacancy_detail'),
    path('vacancies/create/', views.create_vacancy, name='create_vacancy'),

    # Стажировки
    path('internships/', views.internship_list, name='internship_list'),
    path('internships/<int:pk>/', views.internship_detail, name='internship_detail'),
    path('internships/create/', views.create_internship, name='create_internship'),

    # Профиль
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    path('profile/applicant/create/', views.create_applicant_profile, name='create_applicant_profile'),
    path('profile/applicant/update/', views.update_applicant_profile, name='update_applicant_profile'),

    # Модерация (админ)
    path('moderation/', views.moderation_list, name='moderation_list'),
    path('moderation/vacancy/<int:pk>/<str:action>/', views.moderate_vacancy, name='moderate_vacancy'),
    path('moderation/internship/<int:pk>/<str:action>/', views.moderate_internship, name='moderate_internship'),

    # Аналитика (админ)
    path('analytics/', views.analytics, name='analytics'),

    # Чат
    path('chats/', views.chat_list, name='chat_list'),
    path('chats/<int:thread_id>/', views.chat_detail, name='chat_detail'),
    path('chats/create-from-application/<int:application_id>/', views.create_chat_from_application, name='create_chat_from_application'),
    path('chats/create-from-internship/<int:response_id>/', views.create_chat_from_internship_response, name='create_chat_from_internship_response'),

    # ИИ-поиск - основной дашборд
    path('ai-search/', views.ai_search_dashboard, name='ai_search_dashboard'),

    # ИИ-поиск для HR (кандидаты)
    path('ai-search/candidate-profile/create/', views.create_ideal_candidate_profile, name='create_ideal_candidate_profile'),
    path('ai-search/candidate-profile/edit/<int:profile_id>/', views.edit_ideal_candidate_profile, name='edit_ideal_candidate_profile'),
    path('ai-search/candidate-results/<int:profile_id>/', views.ai_candidate_results, name='ai_candidate_results'),

    # ИИ-поиск для соискателей (вакансии)
    path('ai-search/vacancy-profile/create/', views.create_ideal_vacancy_profile, name='create_ideal_vacancy_profile'),
    path('ai-search/vacancy-profile/edit/<int:profile_id>/', views.edit_ideal_vacancy_profile, name='edit_ideal_vacancy_profile'),
    path('ai-search/vacancy-results/<int:profile_id>/', views.ai_vacancy_results, name='ai_vacancy_results'),

    # Общие URLs для ИИ-поиска
    path('ai-search/results/<int:profile_id>/', views.ai_search_results, name='ai_search_results'),
    path('ai-search/run/<int:profile_id>/', views.run_ai_search, name='run_ai_search'),
    path('ai-search/force/<int:profile_id>/', views.force_ai_search, name='force_ai_search'),
    path('ai-search/send-offer/<int:match_id>/', views.send_offer_to_candidate, name='send_offer_to_candidate'),

    # Резюме
    path('applicant/resume/', views.create_or_edit_resume, name='create_or_edit_resume'),
    path('applicant/resume/view/', views.applicant_resume_view, name='applicant_resume_view'),
    path('resume/<int:applicant_id>/', views.applicant_resume_view, name='view_resume'),

    # AJAX URLs
    path('ajax/get-subcategories/', views.get_subcategories, name='get_subcategories'),
    path('ajax/get-skills/', views.get_skills, name='get_skills'),
    path('get-subcategories/', views.get_subcategories, name='get_subcategories'),

    path('analytics/', views.analytics, name='analytics'),
    path('analytics/export/<str:format_type>/', views.export_analytics, name='export_analytics'),

]