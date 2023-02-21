from django import forms
from django.utils import timezone

class ProfileForm(forms.ModelForm):
    language = forms.CharField(max_length=10, required=False)
    timezone = forms.CharField(max_length=50, required=False, initial=timezone.get_default_timezone_name())

    class Meta:
        fields = ['language', 'timezone']
