from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse


# Добавим новую модель для запросов на подтверждение роли
class RoleApprovalRequest(models.Model):
    ROLE_CHOICES = [
        ('hr', 'HR компании'),
        ('university', 'Представитель вуза'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    requested_role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Запрашиваемая роль")
    company_name = models.CharField(max_length=200, blank=True, verbose_name="Название компании")
    institution_name = models.CharField(max_length=200, blank=True, verbose_name="Название учебного заведения")
    status = models.CharField(max_length=20, choices=[
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ], default='pending', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reviewed_requests', verbose_name="Рассмотрено")

    class Meta:
        verbose_name = "Запрос на подтверждение роли"
        verbose_name_plural = "Запросы на подтверждение роли"

    def __str__(self):
        return f"{self.user.username} - {self.get_requested_role_display()}"


class Company(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название компании")
    description = models.TextField(verbose_name="Описание")
    contact_email = models.EmailField(verbose_name="Контактный email")
    contact_phone = models.CharField(max_length=20, verbose_name="Контактный телефон")
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False, verbose_name="Подтверждена")  # Новое поле

    objects = models.Manager()

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"

    def __str__(self):
        return self.name


class EducationalInstitution(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название учебного заведения")
    contact_email = models.EmailField(verbose_name="Контактный email")
    contact_phone = models.CharField(max_length=20, verbose_name="Контактный телефон")
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False, verbose_name="Подтверждено")  # Новое поле

    objects = models.Manager()

    class Meta:
        verbose_name = "Учебное заведение"
        verbose_name_plural = "Учебные заведения"

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    description = models.TextField(blank=True, verbose_name="Описание")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               verbose_name="Родительская категория")
    is_main = models.BooleanField(default=False, verbose_name="Основная категория")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['is_main', 'name']

    def __str__(self):
        return self.name

    def get_subcategories(self):
        """Возвращает все подкатегории"""
        return Category.objects.filter(parent=self)

    def is_subcategory(self):
        """Проверяет, является ли категория подкатегорией"""
        return self.parent is not None


class Vacancy(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('moderation', 'На модерации'),
        ('published', 'Опубликована'),
        ('rejected', 'Отклонена'),
        ('closed', 'Закрыта'),
    ]
    views = models.IntegerField(default=0, verbose_name="Просмотры")
    title = models.CharField(max_length=200, verbose_name="Должность")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Компания")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Категория")
    description = models.TextField(verbose_name="Описание вакансии")
    requirements = models.TextField(verbose_name="Требования")
    salary = models.CharField(max_length=100, blank=True, verbose_name="Зарплата")
    contact_info = models.TextField(verbose_name="Контактная информация")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Статус")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Создатель")
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    auto_close_at = models.DateTimeField(null=True, blank=True, verbose_name="Автоматическое закрытие")

    objects = models.Manager()
    views = models.IntegerField(default=0, verbose_name="Просмотры")
    salary_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        verbose_name="Зарплата (число)")
    location = models.CharField(max_length=200, blank=True, verbose_name="Местоположение")
    employment_type = models.CharField(max_length=50, choices=[
        ('full', 'Полная занятость'),
        ('part', 'Частичная занятость'),
        ('remote', 'Удаленная работа'),
    ], default='full', verbose_name="Тип занятости")

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.company.name}"

    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('vacancy_detail', kwargs={'pk': self.pk})


class Internship(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('moderation', 'На модерации'),
        ('published', 'Опубликована'),
        ('rejected', 'Отклонена'),
        ('closed', 'Закрыта'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название стажировки")
    institution = models.ForeignKey(EducationalInstitution, on_delete=models.CASCADE, verbose_name="Учебное заведение")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Категория")
    specialty = models.CharField(max_length=200, verbose_name="Специальность")
    student_count = models.IntegerField(verbose_name="Количество студентов")
    period = models.CharField(max_length=100, verbose_name="Период стажировки")
    description = models.TextField(verbose_name="Описание")
    requirements = models.TextField(verbose_name="Требования к студентам")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Статус")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Создатель")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        verbose_name = "Стажировка"
        verbose_name_plural = "Стажировки"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.institution.name}"


class Applicant(models.Model):
    EXPERIENCE_LEVELS = [
        ('no_experience', 'Нет опыта'),
        ('intern', 'Стажер'),
        ('junior', 'Junior (Начинающий)'),
        ('middle', 'Middle (Опытный)'),
        ('senior', 'Senior (Старший)'),
        ('lead', 'Lead (Руководитель)'),
    ]

    EDUCATION_LEVELS = [
        ('secondary', 'Среднее'),
        ('secondary_professional', 'Среднее профессиональное'),
        ('high', 'Высшее образование'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Телефон")

    # Обновленные поля для резюме
    position = models.CharField(max_length=200, blank=True, verbose_name="Желаемая должность")
    experience_level = models.CharField(
        max_length=50,
        choices=EXPERIENCE_LEVELS,
        blank=True,
        verbose_name="Уровень опыта"
    )
    education_level = models.CharField(
        max_length=50,
        choices=EDUCATION_LEVELS,
        blank=True,
        verbose_name="Уровень образования"
    )
    skills = models.TextField(blank=True, verbose_name="Навыки")

    # Старые поля оставляем для обратной совместимости
    experience = models.TextField(blank=True, verbose_name="Опыт работы")
    education = models.TextField(blank=True, verbose_name="Образование")
    about = models.TextField(blank=True, verbose_name="О себе")

    resume_file = models.FileField(upload_to='resumes/', null=True, blank=True, verbose_name="Файл резюме")
    resume_text = models.TextField(blank=True, verbose_name="Текст резюме")
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True, verbose_name="Резюме опубликовано")

    class Meta:
        verbose_name = "Соискатель"
        verbose_name_plural = "Соискатели"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_experience_display(self):
        return dict(self.EXPERIENCE_LEVELS).get(self.experience_level, '')

    def get_education_display(self):
        return dict(self.EDUCATION_LEVELS).get(self.education_level, '')

    def get_full_resume_text(self):
        """Возвращает полный текст резюме для поиска с проверкой на пустоту"""
        parts = []

        # Добавляем только заполненные поля
        if self.position:
            parts.append(f"Должность: {self.position}")

        if self.experience_level:
            parts.append(f"Уровень опыта: {self.get_experience_display()}")

        if self.education_level:
            parts.append(f"Уровень образования: {self.get_education_display()}")

        if self.skills and self.skills.strip():
            parts.append(f"Навыки: {self.skills}")

        if self.resume_text and self.resume_text.strip():
            parts.append(f"Резюме: {self.resume_text}")

        # Добавляем старые поля для обратной совместимости
        if self.experience and self.experience.strip():
            parts.append(f"Опыт: {self.experience}")

        if self.education and self.education.strip():
            parts.append(f"Образование: {self.education}")

        if self.about and self.about.strip():
            parts.append(f"О себе: {self.about}")

        # Если все поля пустые, возвращаем хотя бы имя
        if not parts:
            parts.append(f"Соискатель: {self.first_name} {self.last_name}")

        return "\n".join(parts)


class Application(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('reviewed', 'Рассмотрена'),
        ('invited', 'Приглашен'),
        ('rejected', 'Отклонена'),
    ]

    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, verbose_name="Вакансия")
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, verbose_name="Соискатель")
    cover_letter = models.TextField(blank=True, verbose_name="Сопроводительное письмо")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    applied_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=50, default='website', verbose_name="Источник")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP адрес")
    objects = models.Manager()

    class Meta:
        verbose_name = "Отклик"
        verbose_name_plural = "Отклики"
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant} - {self.vacancy.title}"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Администратор ОЭЗ'),
        ('hr', 'HR компании'),
        ('university', 'Представитель вуза'),
        ('applicant', 'Соискатель'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Роль")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Компания")
    institution = models.ForeignKey(EducationalInstitution, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name="Учебное заведение")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    is_approved = models.BooleanField(default=False, verbose_name="Подтвержден")

    objects = models.Manager()

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    def can_access_dashboard(self):
        """Проверяет, может ли пользователь получить доступ к дашборду"""
        # Админы всегда имеют доступ
        if self.role == 'admin':
            return True
        # Соискатели всегда имеют доступ
        if self.role == 'applicant':
            return True
        # HR и университеты требуют подтверждения
        return self.is_approved

    def save(self, *args, **kwargs):
        # Админы автоматически подтверждаются
        if self.role == 'admin':
            self.is_approved = True
        super().save(*args, **kwargs)


class InternshipApplication(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('reviewed', 'Рассмотрена'),
        ('invited', 'Приглашены'),
        ('rejected', 'Отклонена'),
    ]

    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, verbose_name="Стажировка")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Компания")
    contact_person = models.CharField(max_length=200, verbose_name="Контактное лицо")
    contact_email = models.EmailField(verbose_name="Контактный email")
    contact_phone = models.CharField(max_length=20, verbose_name="Контактный телефон")
    proposal = models.TextField(verbose_name="Предложение по стажировке")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отклик на стажировку"
        verbose_name_plural = "Отклики на стажировки"
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.company.name} - {self.internship.title}"


class InternshipResponse(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('reviewed', 'Рассмотрена'),
        ('invited', 'Приглашен'),
        ('rejected', 'Отклонена'),
    ]

    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, verbose_name="Стажировка")
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, verbose_name="Соискатель")
    cover_letter = models.TextField(verbose_name="Сопроводительное письмо")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отклик на стажировку"
        verbose_name_plural = "Отклики на стажировки"
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant} - {self.internship.title}"


# models.py - добавить новые модели
class ChatThread(models.Model):
    """Поток переписки между участниками"""
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, null=True, blank=True)
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, null=True, blank=True)
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    hr_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='hr_chats')
    university_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='university_chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    @classmethod
    def get_or_create_chat(cls, vacancy=None, internship=None, applicant=None, hr_user=None, university_user=None):
        """Создает или возвращает существующий чат"""
        try:
            if vacancy and applicant and hr_user:
                # Ищем существующий чат
                thread = cls.objects.filter(
                    vacancy=vacancy,
                    applicant=applicant,
                    hr_user=hr_user,
                    is_active=True
                ).first()

                if thread:
                    return thread, False
                else:
                    # Создаем новый чат
                    thread = cls.objects.create(
                        vacancy=vacancy,
                        applicant=applicant,
                        hr_user=hr_user,
                        is_active=True
                    )
                    return thread, True

            elif internship and applicant and university_user:
                # Аналогично для стажировок
                thread = cls.objects.filter(
                    internship=internship,
                    applicant=applicant,
                    university_user=university_user,
                    is_active=True
                ).first()

                if thread:
                    return thread, False
                else:
                    thread = cls.objects.create(
                        internship=internship,
                        applicant=applicant,
                        university_user=university_user,
                        is_active=True
                    )
                    return thread, True

            else:
                # Простой чат без привязки к вакансии/стажировке
                thread = cls.objects.filter(
                    applicant=applicant,
                    hr_user=hr_user,
                    is_active=True
                ).first()

                if thread:
                    return thread, False
                else:
                    thread = cls.objects.create(
                        applicant=applicant,
                        hr_user=hr_user,
                        is_active=True
                    )
                    return thread, True

        except Exception as e:
            print(f"Error creating chat: {e}")
            return None, False


    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
        ordering = ['-updated_at']

    def __str__(self):
        if self.vacancy:
            return f"Чат: {self.applicant} - {self.vacancy.title}"
        else:
            return f"Чат: {self.applicant} - {self.internship.title}"

    def get_other_participant(self, current_user):
        """Получить второго участника чата"""
        if current_user == self.applicant.user:
            if self.hr_user:
                return self.hr_user
            elif self.university_user:
                return self.university_user
        return self.applicant.user

    def get_subject(self):
        """Получить тему чата"""
        if self.vacancy:
            return self.vacancy.title
        else:
            return self.internship.title


class ChatMessage(models.Model):
    """Сообщение в чате"""
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(verbose_name="Сообщение")
    file = models.FileField(upload_to='chat_files/', null=True, blank=True, verbose_name="Файл")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Сообщение чата"
        verbose_name_plural = "Сообщения чатов"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.message[:50]}"


# Добавить в models.py после существующих моделей

class IdealCandidateProfile(models.Model):
    """Идеальный профиль кандидата от HR"""
    hr_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="HR")
    title = models.CharField(max_length=200, verbose_name="Название профиля")
    ideal_resume = models.TextField(verbose_name="Идеальное резюме")
    required_skills = models.TextField(verbose_name="Требуемые навыки")
    experience_level = models.CharField(max_length=100, verbose_name="Уровень опыта")
    education_requirements = models.TextField(blank=True, verbose_name="Требования к образованию")
    min_match_percentage = models.IntegerField(default=70, verbose_name="Минимальный % совпадения")
    max_candidates = models.IntegerField(default=10, verbose_name="Максимум кандидатов")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Идеальный профиль кандидата"
        verbose_name_plural = "Идеальные профили кандидатов"

    def __str__(self):
        return f"{self.title} - {self.hr_user.username}"

class SkillTag(models.Model):
    """Теги навыков для категорий"""
    name = models.CharField(max_length=100, verbose_name="Название тега")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Тег навыка"
        verbose_name_plural = "Теги навыков"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"

class EducationLevel(models.Model):
    """Уровни образования"""
    name = models.CharField(max_length=100, verbose_name="Название уровня")
    order = models.IntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Уровень образования"
        verbose_name_plural = "Уровни образования"
        ordering = ['order']

    def __str__(self):
        return self.name



class IdealVacancyProfile(models.Model):
    """Идеальная вакансия от соискателя"""
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, verbose_name="Соискатель")
    title = models.CharField(max_length=200, verbose_name="Название профиля")

    # Новые поля для выбора из списка
    main_category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                      verbose_name="Основная категория", related_name='main_vacancy_profiles')
    subcategory = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name="Подкатегория", related_name='sub_vacancy_profiles')

    # Убрано поле ideal_position
    desired_skills = models.TextField(verbose_name="Желаемые навыки", blank=True)
    selected_skill_tags = models.ManyToManyField(SkillTag, blank=True, verbose_name="Выбранные теги навыков")

    experience_level = models.CharField(max_length=100, verbose_name="Уровень опыта")
    education_level = models.CharField(
        max_length=50,
        choices=Applicant.EDUCATION_LEVELS,
        default='high',
        verbose_name="Уровень образования"
    )

    desired_salary = models.CharField(max_length=100, blank=True, verbose_name="Желаемая зарплата")
    location_preferences = models.CharField(max_length=200, blank=True, verbose_name="Предпочтения по локации")

    # Новое поле для стека технологий
    tech_stack = models.CharField(max_length=500, blank=True, verbose_name="Стек технологий")

    min_match_percentage = models.IntegerField(default=70, verbose_name="Минимальный % совпадения")
    max_vacancies = models.IntegerField(default=10, verbose_name="Максимум вакансий")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Идеальный профиль вакансии"
        verbose_name_plural = "Идеальные профили вакансий"

    def __str__(self):
        return f"{self.title} - {self.applicant}"

    def get_selected_skills_list(self):
        """Возвращает список выбранных навыков"""
        if self.selected_skill_tags.exists():
            return [tag.name for tag in self.selected_skill_tags.all()]
        elif self.desired_skills:
            return [skill.strip() for skill in self.desired_skills.split(',')]
        return []

    def get_education_display(self):
        """Возвращает отображаемое значение уровня образования"""
        return dict(Applicant.EDUCATION_LEVELS).get(self.education_level, '')

class AISearchMatch(models.Model):
    """Результаты сопоставления ИИ"""
    ideal_candidate_profile = models.ForeignKey(IdealCandidateProfile, on_delete=models.CASCADE, null=True, blank=True)
    ideal_vacancy_profile = models.ForeignKey(IdealVacancyProfile, on_delete=models.CASCADE, null=True, blank=True)
    matched_applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, null=True, blank=True)
    matched_vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, null=True, blank=True)
    match_percentage = models.IntegerField(verbose_name="Процент совпадения")
    match_details = models.JSONField(verbose_name="Детали совпадения", default=dict)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Ожидает'),
        ('offer_sent', 'Офер отправлен'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Результат ИИ-поиска"
        verbose_name_plural = "Результаты ИИ-поиска"

    def __str__(self):
        if self.ideal_candidate_profile:
            return f"Кандидат {self.matched_applicant} - {self.match_percentage}%"
        else:
            return f"Вакансия {self.matched_vacancy} - {self.match_percentage}%"


# Добавить в models.py после существующих моделей




