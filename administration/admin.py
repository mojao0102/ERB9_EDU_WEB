from django.contrib import admin
from core.admin import ModelAdminOverride
from .models import Staff, Center, Room

@admin.register(Staff)
class StaffAdmin(ModelAdminOverride):
    list_display = ('staff_no', 'last_name', 'first_name', 'email', 'is_active', 'is_admin')
    list_filter = ('is_active', 'is_admin')
    search_fields = ('staff_no', 'last_name', 'first_name', 'email')
    
    fieldsets = (
        ('基本資料', {'fields': ('staff_no', 'last_name', 'first_name', 'phone', 'email', 'addr')}),
        ('帳號與權限', {'fields': ('username', 'password', 'is_active', 'is_admin', 'remarks')}),
        ('審計紀錄', {'fields': ('file_status', 'created_by', 'created_datetime', 'last_updated_by', 'last_updated_datetime')}),
    )

@admin.register(Center)
class CenterAdmin(ModelAdminOverride):
    list_display = ('name', 'phone', 'email', 'file_status')
    search_fields = ('name', 'phone', 'email')
    
    fieldsets = (
        ('中心資訊', {'fields': ('name', 'phone', 'fax', 'email', 'map_url', 'intro')}),
        ('地址詳情', {'fields': ('addr', 'addr_desc')}),
        ('審計紀錄', {'fields': ('file_status', 'created_by', 'created_datetime', 'last_updated_by', 'last_updated_datetime')}),
    )

@admin.register(Room)
class RoomAdmin(ModelAdminOverride):
    list_display = ('name', 'center', 'desc', 'file_status')
    list_filter = ('center',)
    search_fields = ('name', 'desc')
    
    fieldsets = (
        ('房間資料', {'fields': ('center', 'name', 'desc')}),
        ('審計紀錄', {'fields': ('file_status', 'created_by', 'created_datetime', 'last_updated_by', 'last_updated_datetime')}),
    )
