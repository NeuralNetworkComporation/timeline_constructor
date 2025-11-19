from django import forms
from .models import Timeline, TimelineEvent


class TimelineForm(forms.ModelForm):
    class Meta:
        model = Timeline
        fields = ['title', 'description', 'is_public']  # Убрали color_scheme
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название таймлайна'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опишите ваш таймлайн...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_public'].widget.attrs.update({'class': 'form-check-input'})


class TimelineEventForm(forms.ModelForm):
    class Meta:
        model = TimelineEvent
        fields = ['title', 'description', 'year', 'era', 'event_type', 'importance']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'era': forms.Select(attrs={'class': 'form-select'}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'importance': forms.Select(attrs={'class': 'form-select'}),
        }