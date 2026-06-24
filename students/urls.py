from django.urls import path
from . import views

# From config/url.py 
# path('manage/students/', include('students.urls', namespace='students')),

app_name = 'students'

urlpatterns = [
    path('list/', views.student_list, name='student_list'),
    path('create/', views.student_edit, name='student_create'),
    path('edit/<str:hash_student>/', views.student_edit, name='student_edit'),
    path('view/<str:hash_student>/', views.student_view, name='student_view'),
    path('delete/<str:hash_student>/', views.student_delete, name='student_delete'),
    ]