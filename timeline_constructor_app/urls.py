from django.contrib.auth import views as auth_views
from . import views
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Аутентификация
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Таймлайны
    path('dashboard/', views.dashboard, name='dashboard'),
    path('timeline/create/', views.timeline_create, name='timeline_create'),
    path('timeline/<int:pk>/', views.timeline_detail, name='timeline_detail'),
    path('timeline/<int:pk>/edit/', views.timeline_edit, name='timeline_edit'),
    path('timeline/<int:pk>/delete/', views.timeline_delete, name='timeline_delete'),
    path('timeline/<int:pk>/settings/', views.timeline_settings, name='timeline_settings'),
    path('timeline/<int:pk>/export/', views.timeline_export, name='timeline_export'),
    path('timeline/<int:pk>/duplicate/', views.timeline_duplicate, name='timeline_duplicate'),

    # События
    path('timeline/<int:timeline_pk>/event/create/', views.event_create, name='event_create'),
    path('event/<int:pk>/edit/', views.event_edit, name='event_edit'),
    path('event/<int:pk>/delete/', views.event_delete, name='event_delete'),

    # Взаимодействие
    path('timeline/<int:pk>/like/', views.like_timeline, name='like_timeline'),
    path('timeline/<int:pk>/comment/', views.add_comment, name='add_comment'),

    # Поиск и статистика
    path('timelines/', views.timeline_list, name='timeline_list'),
    path('search/', views.timeline_search, name='timeline_search'),
    path('statistics/', views.timeline_statistics, name='timeline_statistics'),

    # Импорт/экспорт
    path('timeline/import/', views.timeline_import, name='timeline_import'),
    path('timeline/<int:pk>/export/download/', views.timeline_export_download, name='timeline_export_download'),

    # Board URLs
    path('board/node/create/', views.create_board_node, name='create_board_node'),
    path('board/node/<int:node_id>/update/', views.update_board_node, name='update_board_node'),
    path('board/node/<int:node_id>/delete/', views.delete_board_node, name='delete_board_node'),

    path('board/', views.board_view, name='board'),
    path('board/timeline/create/', views.board_create_timeline, name='board_create_timeline'),
    path('board/node/<int:node_id>/update/', views.update_board_node, name='update_board_node'),
    path('board/node/<int:node_id>/delete/', views.delete_board_node, name='delete_board_node'),
]