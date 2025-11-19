from django.contrib import admin
from .models import *

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_email', 'contact_phone', 'created_at']
    search_fields = ['name']

@admin.register(EducationalInstitution)
class EducationalInstitutionAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_email', 'contact_phone', 'created_at']
    search_fields = ['name']

@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'status', 'created_at']
    list_filter = ['status', 'company', 'created_at']
    search_fields = ['title', 'company__name']

@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    list_display = ['title', 'institution', 'status', 'created_at']
    list_filter = ['status', 'institution', 'created_at']
    search_fields = ['title', 'institution__name']

@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'created_at']
    search_fields = ['first_name', 'last_name', 'email']

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'vacancy', 'status', 'applied_at']
    list_filter = ['status', 'applied_at']
    search_fields = ['applicant__first_name', 'applicant__last_name', 'vacancy__title']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'company', 'institution']
    list_filter = ['role']
    search_fields = ['user__username']

@admin.register(InternshipResponse)
class InternshipResponseAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'internship', 'status', 'applied_at']
    list_filter = ['status', 'applied_at']
    search_fields = ['applicant__first_name', 'applicant__last_name', 'internship__title']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']