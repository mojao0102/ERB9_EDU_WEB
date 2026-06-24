# courses/forms.py
from django import forms
from .models import Course, CourseTemplate
from django.utils import timezone
from datetime import timedelta

class CourseTemplateForm(forms.ModelForm):
    class Meta:
        model = CourseTemplate
        fields = [
            'sub_category', 'teacher', 'name', 'content',
            'feature_1', 'feature_2', 'feature_3', 'feature_4',
            'feature_5', 'feature_6', 'feature_7', 'feature_8',
            'total_lessons', 'hours_per_lesson', 'total_hours', 'course_fee'
        ]