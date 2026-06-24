from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('list/', views.teacher_list, name='teacher_list'),
    path('create/', views.teacher_edit, name='teacher_create'),
    path('edit/<str:hash_teacher>', views.teacher_edit, name='teacher_edit'),
    path('view/<str:hash_teacher>', views.teacher_view, name='teacher_view'),
]
