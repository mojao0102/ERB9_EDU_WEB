# teachers/forms.py
from django import forms
from .models import Teacher

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['username', 'password', 'teacher_no', 'first_name', 'last_name', 'title', 'phone', 'email', 'remarks', 'is_active']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        list_teacher = Teacher.objects.filter(username=username).exclude(file_status='deleted')
        if self.instance and self.instance.pk:
            list_teacher = list_teacher.exclude(pk=self.instance.pk)
        
        if list_teacher.exists():
            raise forms.ValidationError("此帳號已被使用，請更換一個帳號")
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 6:
            raise forms.ValidationError("密碼長度至少需要 6 個字元")
        return password