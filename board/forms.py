from django import forms
from .models import BoardTimeline, BoardSettings


class BoardTimelineForm(forms.ModelForm):
    """Форма создания/редактирования таймлайна на доске"""
    class Meta:
        model = BoardTimeline
        fields = ['title', 'description', 'color', 'background_color', 'border_color']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название таймлайна',
                'autocomplete': 'off'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Описание (необязательно)',
                'rows': 3,
                'autocomplete': 'off'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color',
                'title': 'Выберите цвет заголовка'
            }),
            'background_color': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color',
                'value': '#ffffff',
                'title': 'Выберите цвет фона'
            }),
            'border_color': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color',
                'value': '#10b981',
                'title': 'Выберите цвет рамки'
            }),
        }


class QuickCreateForm(forms.Form):
    """Быстрая форма создания таймлайна"""
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Название таймлайна',
            'autofocus': True
        })
    )
    color = forms.CharField(
        max_length=20,
        initial='#10b981',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'color',
            'title': 'Цвет'
        })
    )


class BoardSettingsForm(forms.ModelForm):
    """Форма настроек доски"""
    class Meta:
        model = BoardSettings
        fields = ['show_grid', 'grid_size', 'grid_color', 'snap_to_grid', 'board_background']
        widgets = {
            'grid_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 10,
                'max': 200,
                'step': 5
            }),
            'grid_color': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color'
            }),
            'board_background': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color'
            }),
        }