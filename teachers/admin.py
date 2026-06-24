from django.contrib import admin
from core.admin import ModelAdminOverride
from .models import Teacher

@admin.register(Teacher)
class TeacherAdmin(ModelAdminOverride):
    list_display = ('teacher_no', 'last_name', 'first_name', 'phone', 'email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('teacher_no', 'last_name', 'first_name', 'email', 'phone')
    list_per_page = 25

    fieldsets = (
        ('導師基本資料', {'fields': ('teacher_no', 'title', 'last_name', 'first_name', 'dob', 'phone', 'email', 'addr')}),
        ('系統帳號設定', {'fields': ('username', 'password', 'is_active', 'remarks')}),
        ('審計紀錄', {'fields': ('file_status', 'created_by', 'created_datetime', 'last_updated_by', 'last_updated_datetime')}),
    )
