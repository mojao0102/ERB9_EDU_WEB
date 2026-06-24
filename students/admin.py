from django.contrib import admin
from core.admin import ModelAdminOverride
from .models import Student

admin.__name__ = "hihi"

@admin.register(Student)
class StudentAdmin(ModelAdminOverride):
    list_display = ('student_no', 'cn_name', 'en_name', 'dob', 'contact1_relationship', 'contact1_phone',
    # 'created_datetime',-
)

    search_fields = ('student_no', 'cn_name', 'en_name', 'email', 'contact1_phone', 'contact2_phone',)
