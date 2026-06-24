from django.contrib import admin
from core.admin import ModelAdminOverride
from .models import News

@admin.register(News)
class NewsAdmin(ModelAdminOverride):
    list_display = ('title', 'publish_date', 'expiry_date', 'is_publish')
    list_filter = ('is_publish', 'publish_date')
    search_fields = ('title', 'desc')
    list_per_page = 25
    
    fieldsets = (
        ('最新消息內容', {'fields': ('title', 'desc', 'publish_date', 'expiry_date', 'is_publish')}),
        ('圖片上傳紀錄', {'fields': ('list_photo', 'photo_1', 'photo_2', 'photo_3')}),
        ('審計紀錄', {'fields': ('file_status', 'created_by', 'created_datetime', 'last_updated_by', 'last_updated_datetime')}),
    )