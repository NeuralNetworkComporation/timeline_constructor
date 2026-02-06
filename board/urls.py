from django.urls import path
from . import views

urlpatterns = [
    path('', views.board_view, name='board'),
    path('timeline/create/', views.create_timeline, name='create_timeline'),
    path('timeline/<int:timeline_id>/update/', views.update_timeline_position, name='update_timeline'),
    path('timeline/<int:timeline_id>/delete/', views.delete_timeline, name='delete_timeline'),
    path('connection/create/', views.create_connection, name='create_connection'),
    path('save-state/', views.save_board_state, name='save_board_state'),
]