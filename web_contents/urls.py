from django.urls import path
from . import views

app_name = 'web_contents'

urlpatterns = [
    path('list/', views.news_list, name='news_list'),
    path('create/', views.news_create, name='news_create'),
    path('edit/<str:hash_news>', views.news_edit, name='news_edit'),
    path('delete/<str:hash_news>/', views.news_delete, name='news_delete'), 
]