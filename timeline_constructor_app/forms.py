from django import forms
from .models import Timeline, TimelineEvent, TimelineComment


class TimelineForm(forms.ModelForm):
    class Meta:
        model = Timeline
        fields = ['title', 'description', 'is_public', 'color_scheme', 'layout',
                  'show_dates', 'show_images', 'allow_comments']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Описание...'}),
            'color_scheme': forms.Select(attrs={'class': 'form-select'}),
            'layout': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['is_public', 'show_dates', 'show_images', 'allow_comments']:
            self.fields[field].widget.attrs['class'] = 'form-check-input'


class TimelineEventForm(forms.ModelForm):
    class Meta:
        model = TimelineEvent
        fields = ['title', 'description', 'detailed_description', 'year', 'month', 'day',
                  'era', 'event_type', 'importance', 'image', 'source_link', 'location', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Описание...'}),
            'detailed_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Подробнее...'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': '-3000', 'max': '2100'}),
            'month': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '12'}),
            'day': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '31'}),
            'era': forms.Select(attrs={'class': 'form-select'}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'importance': forms.Select(attrs={'class': 'form-select'}),
            'source_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Местоположение'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'тег1, тег2...'}),
        }


class TimelineCommentForm(forms.ModelForm):
    class Meta:
        model = TimelineComment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Комментарий...'}),
        }


class TimelineSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Поиск...'})
    )
    era = forms.ChoiceField(
        required=False,
        choices=[('', 'Все эпохи')] + TimelineEvent.ERA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    event_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Все типы')] + TimelineEvent.EVENT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class TimelineImportForm(forms.Form):
    json_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.json'}),
    )

    def clean_json_file(self):
        import json
        from django.core.exceptions import ValidationError
        file = self.cleaned_data.get('json_file')
        if file:
            try:
                json.loads(file.read().decode('utf-8'))
                file.seek(0)
                return file
            except json.JSONDecodeError:
                raise ValidationError('Невалидный JSON')
        return file


class TimelineSettingsForm(forms.ModelForm):
    class Meta:
        model = Timeline
        fields = ['color_scheme', 'layout', 'show_dates', 'show_images', 'allow_comments', 'is_public']
        widgets = {
            'color_scheme': forms.Select(attrs={'class': 'form-select'}),
            'layout': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['show_dates', 'show_images', 'allow_comments', 'is_public']:
            self.fields[field].widget.attrs['class'] = 'form-check-input'