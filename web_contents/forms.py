from django import forms
from .models import News

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = [
            'title', 'desc', 'publish_date', 'expiry_date',
            'is_publish', 'list_photo', 'photo_1', 'photo_2', 'photo_3'
        ]
        widgets = {
            'publish_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expiry_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }