from django.urls import path
from .views import auth_views, course_views, dashboard_views, payment_views, views, calendar_view

app_name = 'front_web'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('newses/', views.newses, name='newses'),
    path('newses/<str:hash_news>', views.news, name='news'),

    path('login/', auth_views.student_login, name='student_login'),
    path('logout/', auth_views.student_logout, name='student_logout'),
    path('register/', auth_views.student_register, name='student_register'),
    path('edit_userinfo/', auth_views.student_edit_info, name='student_edit_info'),
    path('change_password/', auth_views.student_change_password, name='student_change_password'),
    path('forget_password/', auth_views.student_forget_password, name='student_forget_password'),
    path('reset_password/<str:uidb64>/<str:token>/', auth_views.student_reset_password, name='student_reset_password'),
    path('register/pending/', auth_views.student_register_pending, name='student_register_pending'),
    path('register/change-email/', auth_views.student_change_email_and_resend, name='student_change_email_and_resend'),
    path('emailverify/<str:uidb64>/<str:token>/', auth_views.student_verifiy_email, name='student_verifiy_email'),

    path('course_list/<str:hash_mc>/', course_views.course_list, name='course_list'),
    path('course/<str:hash_course>/', course_views.course, name='course'),

    path('course/<str:hash_course>/pay/', payment_views.course_payment, name='course_payment'),
    path('payment_successful/', payment_views.payment_successful, name='payment_successful'),
    path('payment_fail/', payment_views.payment_fail, name='payment_fail'),
    path('stripe/webhook/', payment_views.stripe_webhook, name='stripe_webhook'),

    path('student_dashboard/', dashboard_views.student_dashboard, name='student_dashboard'),
    path('student_dashboard/payment_receipt/<str:hash_signup>/', dashboard_views.download_payment_receipt, name='download_payment_receipt'),
    path('student_dashboard/refund_receipt/<str:hash_refund>/', dashboard_views.download_refund_receipt, name='download_refund_receipt'),

    # 行事曆新增路由
    path("student/my-calendar/", calendar_view.student_calendar_page, name="student_my_calendar"),
    path("student/api/calendar-events/", calendar_view.StudentCalendarEventAPI.as_view(), name="student_calendar_events"),
]
