from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Основные URLs
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Dashboard и управление таймлайнами
    path('dashboard/', views.dashboard, name='dashboard'),
    path('timeline/create/', views.timeline_create, name='timeline_create'),
    path('timeline/<int:pk>/edit/', views.timeline_edit, name='timeline_edit'),
    path('timeline/<int:pk>/', views.timeline_detail, name='timeline_detail'),
    path('timeline/<int:pk>/delete/', views.timeline_delete, name='timeline_delete'),

    # События
    path('timeline/<int:timeline_pk>/event/create/', views.event_create, name='event_create'),
    path('event/<int:pk>/delete/', views.event_delete, name='event_delete'),

    # Поиск и список
    path('timelines/', views.timeline_list, name='timeline_list'),
]

# Временно закомментируем неработающие URLs:
# path('event/<int:pk>/edit/', views.event_edit, name='event_edit'),
# path('timeline/<int:timeline_pk>/comment/', views.add_comment, name='add_comment'),
# path('timeline/<int:timeline_pk>/collaborator/', views.add_collaborator, name='add_collaborator'),
# path('timeline/<int:timeline_pk>/collaborator/<int:user_pk>/remove/', views.remove_collaborator, name='remove_collaborator'),
# path('timeline/<int:pk>/export/', views.timeline_export, name='timeline_export'),
# path('timeline/<int:pk>/duplicate/', views.timeline_duplicate, name='timeline_duplicate'),
# path('search/', views.timeline_search, name='timeline_search'),