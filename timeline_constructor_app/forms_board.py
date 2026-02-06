from django import forms
from .models_board import BoardTimeline, BoardConnection


class BoardTimelineForm(forms.ModelForm):
    class Meta:
        model = BoardTimeline
        fields = ['title', 'description', 'color']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название таймлайна'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание (необязательно)'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#10b981'
            })
        }