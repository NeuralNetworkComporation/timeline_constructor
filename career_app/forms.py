from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    role = forms.ChoiceField(
        choices=[
            ('applicant', 'Соискатель'),
            ('hr', 'HR компании'),
            ('university', 'Представитель вуза'),
            # Админ убран из выбора при регистрации
        ],
        label="Роль в системе",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    company_name = forms.CharField(
        max_length=200,
        required=False,
        label="Название компании",
        help_text="Заполните, если выбрали роль HR компании",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    institution_name = forms.CharField(
        max_length=200,
        required=False,
        label="Название учебного заведения",
        help_text="Заполните, если выбрали роль представителя вуза",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role', 'company_name', 'institution_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        company_name = cleaned_data.get('company_name')
        institution_name = cleaned_data.get('institution_name')

        if role == 'hr' and not company_name:
            raise forms.ValidationError("Для роли HR компании необходимо указать название компании")
        if role == 'university' and not institution_name:
            raise forms.ValidationError("Для роли представителя вуза необходимо указать название учебного заведения")

        return cleaned_data


class RoleSelectionForm(forms.Form):
    ROLE_CHOICES = [
        ('applicant', 'Соискатель'),
        ('hr', 'HR компании'),
        ('university', 'Представитель вуза'),
        ('admin', 'Администратор ОЭЗ'),
    ]

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label="Выберите роль для входа",
        widget=forms.RadioSelect
    )


class CustomLoginForm(forms.Form):
    username = forms.CharField(label="Логин")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'phone': 'Телефон',
        }

class ApplicantForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
            'phone': 'Телефон',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Автозаполнение из пользователя, если instance не существует
        if not self.instance.pk and hasattr(self, 'user'):
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

class VacancyForm(forms.ModelForm):
    # Поля для выбора категорий
    main_category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_main=True),
        required=True,
        label="Основная категория",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_main_category'})
    )

    subcategory = forms.ModelChoiceField(
        queryset=Category.objects.none(),  # Будет заполняться динамически
        required=True,
        label="Подкатегория",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_subcategory'})
    )

    location = forms.CharField(
        max_length=200,
        required=True,
        label="Местоположение",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Например: Москва, удаленно, гибридный формат'})
    )

    class Meta:
        model = Vacancy
        fields = ['title', 'main_category', 'subcategory', 'description', 'requirements', 'salary', 'location']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'salary': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: от 100000 руб.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Обрабатываем данные POST для инициализации queryset
        if 'main_category' in self.data:
            try:
                main_category_id = int(self.data.get('main_category'))
                self.fields['subcategory'].queryset = Category.objects.filter(
                    parent_id=main_category_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.category:
            # Если редактируем существующую вакансию
            if self.instance.category.parent:
                self.fields['main_category'].initial = self.instance.category.parent
                self.fields['subcategory'].queryset = Category.objects.filter(
                    parent=self.instance.category.parent
                )
            else:
                self.fields['main_category'].initial = self.instance.category
                self.fields['subcategory'].queryset = Category.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        main_category = cleaned_data.get('main_category')
        subcategory = cleaned_data.get('subcategory')

        if main_category and subcategory:
            # Проверяем, что подкатегория принадлежит выбранной основной категории
            if subcategory.parent != main_category:
                self.add_error('subcategory', "Выбранная подкатегория не принадлежит выбранной основной категории")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        subcategory = self.cleaned_data.get('subcategory')
        if subcategory:
            instance.category = subcategory

        if commit:
            instance.save()
        return instance


class InternshipForm(forms.ModelForm):
    # Поля для выбора категорий
    main_category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_main=True),
        required=True,
        label="Основная категория",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_main_category'})
    )

    subcategory = forms.ModelChoiceField(
        queryset=Category.objects.none(),  # Будет заполняться динамически
        required=True,
        label="Подкатегория",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_subcategory'})
    )

    location = forms.CharField(
        max_length=200,
        required=True,
        label="Место стажировки",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Например: Москва, удаленно, офис компании'})
    )

    class Meta:
        model = Internship
        fields = ['title', 'main_category', 'subcategory', 'student_count', 'period', 'description', 'requirements',
                  'location']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'student_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'period': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: 3 месяца, лето 2024'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Обрабатываем данные POST для инициализации queryset
        if 'main_category' in self.data:
            try:
                main_category_id = int(self.data.get('main_category'))
                self.fields['subcategory'].queryset = Category.objects.filter(
                    parent_id=main_category_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.category:
            # Если редактируем существующую стажировку
            if self.instance.category.parent:
                self.fields['main_category'].initial = self.instance.category.parent
                self.fields['subcategory'].queryset = Category.objects.filter(
                    parent=self.instance.category.parent
                )
            else:
                self.fields['main_category'].initial = self.instance.category
                self.fields['subcategory'].queryset = Category.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        main_category = cleaned_data.get('main_category')
        subcategory = cleaned_data.get('subcategory')

        if main_category and subcategory:
            # Проверяем, что подкатегория принадлежит выбранной основной категории
            if subcategory.parent != main_category:
                self.add_error('subcategory', "Выбранная подкатегория не принадлежит выбранной основной категории")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        subcategory = self.cleaned_data.get('subcategory')
        if subcategory:
            instance.category = subcategory

        if commit:
            instance.save()
        return instance



class InternshipResponseForm(forms.ModelForm):
    class Meta:
        model = InternshipResponse
        fields = ['cover_letter']


class AdminPromotionForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Пользователь",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Исключаем пользователей, которые уже админы
        admin_users = UserProfile.objects.filter(role='admin').values_list('user_id', flat=True)
        self.fields['user'].queryset = User.objects.exclude(id__in=admin_users)


# forms.py - добавить новые формы
class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['message', 'file']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Введите ваше сообщение...',
                'class': 'form-control'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'message': 'Сообщение',
            'file': 'Прикрепить файл'
        }

# Добавить в forms.py

class IdealCandidateProfileForm(forms.ModelForm):
    EXPERIENCE_LEVELS = [
        ('', '--- Выберите уровень ---'),
        ('junior', 'Junior (Начинающий)'),
        ('middle', 'Middle (Опытный)'),
        ('senior', 'Senior (Старший)'),
        ('lead', 'Lead (Руководитель)'),
    ]

    experience_level = forms.ChoiceField(
        choices=EXPERIENCE_LEVELS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Уровень опыта'
    )

    class Meta:
        model = IdealCandidateProfile
        fields = [
            'title', 'ideal_resume', 'required_skills', 'experience_level',
            'education_requirements', 'min_match_percentage', 'max_candidates'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Старший Python разработчик'}),
            'ideal_resume': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Опишите идеального кандидата: навыки, опыт, образование, личные качества...'
            }),
            'required_skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Python, Django, REST API, Docker, PostgreSQL, лидерство'
            }),
            'education_requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Требования к образованию (необязательно)'
            }),
            'min_match_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '10',
                'max': '100',
                'value': '70'
            }),
            'max_candidates': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '50',
                'value': '10'
            }),
        }
        labels = {
            'title': 'Название профиля',
            'ideal_resume': 'Идеальное резюме',
            'required_skills': 'Требуемые навыки',
            'education_requirements': 'Требования к образованию',
            'min_match_percentage': 'Минимальный процент совпадения (%)',
            'max_candidates': 'Количество кандидатов для поиска',
        }


class IdealVacancyProfileForm(forms.ModelForm):
    EXPERIENCE_LEVELS = [
        ('', '--- Выберите уровень ---'),
        ('intern', 'Стажер'),
        ('junior', 'Junior (Начинающий)'),
        ('middle', 'Middle (Опытный)'),
        ('senior', 'Senior (Старший)'),
        ('lead', 'Lead (Руководитель)'),
    ]

    EDUCATION_LEVELS = [
        ('', '--- Выберите уровень образования ---'),
        ('secondary', 'Среднее'),
        ('secondary_professional', 'Среднее профессиональное'),
        ('high', 'Высшее образование'),
    ]

    # Поля для выбора категорий
    main_category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_main=True),
        required=True,
        label="Основная категория",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_main_category'})
    )

    subcategory = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=True,
        label="Подкатегория",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_subcategory'})
    )

    # Поле для выбора тегов
    selected_skill_tags = forms.ModelMultipleChoiceField(
        queryset=SkillTag.objects.none(),
        required=False,
        label="Выберите навыки (максимум 10)",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'skill-tags-checkbox'}),
        help_text="Выберите до 10 наиболее важных для вас навыков"
    )

    experience_level = forms.ChoiceField(
        choices=EXPERIENCE_LEVELS,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Уровень опыта'
    )

    education_level = forms.ChoiceField(
        choices=EDUCATION_LEVELS,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Уровень образования'
    )

    tech_stack = forms.CharField(
        required=False,
        max_length=500,
        label="Стек технологий",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: Python, Django, React, PostgreSQL, Docker...'
        }),
        help_text="Перечислите технологии, с которыми хотите работать"
    )

    class Meta:
        model = IdealVacancyProfile
        fields = [
            'title', 'main_category', 'subcategory',
            'selected_skill_tags', 'experience_level', 'education_level',
            'desired_salary', 'location_preferences', 'tech_stack',
            'min_match_percentage', 'max_vacancies'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Удаленная работа Python разработчиком'
            }),
            'desired_salary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Пример: от 100000 руб.'
            }),
            'location_preferences': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Пример: Москва, удаленно, гибридный формат'
            }),
            'min_match_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '10',
                'max': '100',
                'value': '70'
            }),
            'max_vacancies': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '50',
                'value': '10'
            }),
        }
        labels = {
            'title': 'Название профиля',
            'desired_salary': 'Желаемая зарплата',
            'location_preferences': 'Предпочтения по локации',
            'min_match_percentage': 'Минимальный процент совпадения (%)',
            'max_vacancies': 'Количество вакансий для поиска',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Обрабатываем данные POST для инициализации queryset
        if 'main_category' in self.data:
            try:
                main_category_id = int(self.data.get('main_category'))
                self.fields['subcategory'].queryset = Category.objects.filter(
                    parent_id=main_category_id
                ).order_by('name')

                # Также загружаем навыки для выбранной подкатегории
                if 'subcategory' in self.data:
                    subcategory_id = self.data.get('subcategory')
                    if subcategory_id:
                        self.fields['selected_skill_tags'].queryset = SkillTag.objects.filter(
                            category_id=subcategory_id
                        )
            except (ValueError, TypeError):
                pass
        elif self.instance and self.instance.pk:
            # Если редактируем существующий профиль
            if self.instance.subcategory:
                self.fields['main_category'].initial = self.instance.subcategory.parent
                self.fields['subcategory'].queryset = Category.objects.filter(
                    parent=self.instance.subcategory.parent
                )
                self.fields['selected_skill_tags'].queryset = SkillTag.objects.filter(
                    category=self.instance.subcategory
                )
            else:
                self.fields['subcategory'].queryset = Category.objects.none()
                self.fields['selected_skill_tags'].queryset = SkillTag.objects.none()
        else:
            self.fields['subcategory'].queryset = Category.objects.none()
            self.fields['selected_skill_tags'].queryset = SkillTag.objects.none()

    def clean_selected_skill_tags(self):
        tags = self.cleaned_data.get('selected_skill_tags')
        if tags and len(tags) > 10:
            raise forms.ValidationError("Можно выбрать не более 10 навыков")
        return tags

    def clean(self):
        cleaned_data = super().clean()
        main_category = cleaned_data.get('main_category')
        subcategory = cleaned_data.get('subcategory')

        if subcategory and main_category:
            if subcategory.parent != main_category:
                raise forms.ValidationError("Выбранная подкатегория не принадлежит выбранной основной категории")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Сохраняем стек технологий в desired_skills для обратной совместимости
        tech_stack = self.cleaned_data.get('tech_stack', '')
        if tech_stack:
            instance.desired_skills = tech_stack

        if commit:
            instance.save()
            self.save_m2m()  # Сохраняем ManyToMany поля

        return instance

class ApplicantResumeForm(forms.ModelForm):
    EXPERIENCE_LEVELS = [
        ('', '--- Выберите уровень опыта ---'),
        ('no_experience', 'Нет опыта'),
        ('intern', 'Стажер'),
        ('junior', 'Junior (Начинающий)'),
        ('middle', 'Middle (Опытный)'),
        ('senior', 'Senior (Старший)'),
        ('lead', 'Lead (Руководитель)'),
    ]

    EDUCATION_LEVELS = [
        ('', '--- Выберите уровень образования ---'),
        ('secondary', 'Среднее'),
        ('secondary_professional', 'Среднее профессиональное'),
        ('high', 'Высшее образование'),
    ]

    experience_level = forms.ChoiceField(
        choices=EXPERIENCE_LEVELS,
        required=True,
        label="Уровень опыта",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    education_level = forms.ChoiceField(
        choices=EDUCATION_LEVELS,
        required=True,
        label="Уровень образования",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Applicant
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'position', 'experience_level', 'education_level', 'skills',
            'resume_text', 'is_published'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control bg-light',
                'readonly': 'readonly',
                'style': 'color: #6c757d;'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control bg-light',
                'readonly': 'readonly',
                'style': 'color: #6c757d;'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control bg-light',
                'readonly': 'readonly',
                'style': 'color: #6c757d;'
            }),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Пример: Python разработчик, Маркетолог, Менеджер проектов'
            }),
            'skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ключевые навыки: Python, Django, английский язык, управление проектами...'
            }),
            'resume_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Опишите ваш опыт работы, образование, достижения, проекты...'
            }),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_published': 'Разрешить компаниям находить мое резюме в поиске',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Автозаполнение данных из профиля пользователя
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Создаем текстовое представление опыта и образования для поиска
        experience_display = dict(self.EXPERIENCE_LEVELS).get(self.cleaned_data['experience_level'], '')
        education_display = dict(self.EDUCATION_LEVELS).get(self.cleaned_data['education_level'], '')

        instance.experience = f"Уровень опыта: {experience_display}"
        instance.education = f"Уровень образования: {education_display}"

        if commit:
            instance.save()
        return instance