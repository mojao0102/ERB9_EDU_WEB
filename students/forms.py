# students/forms.py
from django import forms
from .models import Student

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'username', 'password', 'is_active', 'student_no',
            'cn_name', 'en_name', 'dob', 'school', 'email',
            'contact1_name', 'contact1_relationship', 'contact1_phone',
            'contact2_name', 'contact2_relationship', 'contact2_phone',
            'remarks'
        ]
        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            print(1)
            self.fields['student_no'].required = False

    def clean_is_active(self):
        is_active = self.cleaned_data.get('is_active', False)
        return is_active
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        qs = Student.objects.filter(username=username).exclude(file_status='deleted')
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("此登入帳號已被使用，請更換一個")
        return username

    def clean_student_no(self):
        student_no = self.cleaned_data.get('student_no')
        if not student_no:
            return student_no         
        qs = Student.objects.filter(student_no=student_no).exclude(file_status='deleted')
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("此學生編號已存在，請確認是否重複建檔")
        return student_no

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 6:
            raise forms.ValidationError("密碼長度至少需要 6 個字元")
        return password

    def save(self, commit=True):
        student = super().save(commit=False)
            
        if commit:
            student.save()
        return student