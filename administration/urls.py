from django.urls import path
from . import views

app_name = 'administration'

urlpatterns = [
    path('login/', views.staff_login, name='staff_login'),
    path('logout/', views.staff_logout, name='staff_logout'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('transactions/export/csv/', views.transaction_export_csv, name='transaction_export_csv'),
    path('transactions/export/pdf/', views.transaction_export_pdf, name='transaction_export_pdf'),
]
