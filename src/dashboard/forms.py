from django import forms
from .models import Map_img
from django.forms import ClearableFileInput


class MapUpload(forms.ModelForm):
    class Meta:
        model = Map_img
        fields = ['img']
        widgets = {
            'img': ClearableFileInput(attrs={'multiple': True}),
        }
