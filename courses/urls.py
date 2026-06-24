from django.urls import path
from .views import course_base, course_template, course_action


app_name = 'courses'

urlpatterns = [
    path('template/', course_template.coursetemp_list, name='coursetemp_list'),
    path('template/create/', course_template.coursetemp_create, name='coursetemp_create'),
    path('template/edit/<str:hash_template>/', course_template.coursetemp_edit, name='coursetemp_edit'),
    path('template/delete/<str:hash_template>/', course_template.coursetemp_delete, name='coursetemp_delete'),
    
    path('list/', course_base.course_list, name='course_list'),
    path('create/', course_base.course_create, name='course_create'),
    path('edit/<str:hash_course>/', course_base.course_edit, name='course_edit'),
    path('view/<str:hash_course>/', course_base.course_view, name='course_view'),

    path('download_payment_receipt/<str:hash_signup>/', course_action.download_payment_receipt, name='download_payment_receipt'),
    path('download_refund_receipt/<str:hash_refund>/', course_action.download_refund_receipt, name='download_refund_receipt'),

    path('publish/set/', course_action.course_set_publish, name='course_set_publish'),
    path('publish/undo/', course_action.course_undo_publish, name='course_undo_publish'),
    path('promote/set/', course_action.course_set_promote, name='course_set_promote'),
    path('promote/undo/', course_action.course_undo_promote, name='course_undo_promote'),
    
    path('signup/<str:hash_signup>/cancel/', course_action.course_cancel_signup, name='course_cancel_signup'),
    path('signup/<str:hash_signup>/refund/', course_action.course_refund_signup, name='course_refund_signup'),
    path('<str:hash_course>/schedule/generate/', course_action.course_generate_schedule, name='course_generate_schedule'),
    path('<str:hash_course>/schedule/create/', course_action.course_create_schedule, name='course_create_schedule'),
    path('schedule/<str:hash_schedule>/edit/', course_action.course_edit_schedule, name='course_edit_schedule'),
    path('schedule/<str:hash_schedule>/delete/', course_action.course_delete_schedule, name='course_delete_schedule'),    
]