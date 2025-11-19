import os
import django
import sys

# Добавляем путь к проекту
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'techno_work.settings')
django.setup()

from django.contrib.auth.models import User
from career_app.models import UserProfile, Company, EducationalInstitution


def create_initial_data():
    print("🚀 Создание начальных данных...")

    # Создаем суперпользователя если его нет
    if not User.objects.filter(username='admin_oez').exists():
        superuser = User.objects.create_superuser(
            username='admin',
            email='a9266730672@yandex.ru',
            password='12345'
        )
        UserProfile.objects.create(
            user=superuser,
            role='admin'
        )
        print("✅ Суперпользователь создан: admin / 12345")
    else:
        # Если пользователь уже есть, создаем для него профиль
        superuser = User.objects.get(username='admin_oez')
        if not hasattr(superuser, 'userprofile'):
            UserProfile.objects.create(
                user=superuser,
                role='admin'
            )
            print("✅ Профиль создан для существующего пользователя admin_oez")

    # Создаем тестовые компании
    companies_data = [
        {'name': 'ТехноКомп', 'email': 'hr@technocomp.ru', 'phone': '+7-495-111-11-11'},
        {'name': 'ИнноТех', 'email': 'career@innotech.ru', 'phone': '+7-495-222-22-22'},
        {'name': 'БиоТех', 'email': 'hr@biotech.ru', 'phone': '+7-495-333-33-33'},
    ]

    for company_data in companies_data:
        company, created = Company.objects.get_or_create(
            name=company_data['name'],
            defaults={
                'contact_email': company_data['email'],
                'contact_phone': company_data['phone'],
                'description': f"Компания-резидент ОЭЗ «Технополис Москва» - {company_data['name']}"
            }
        )
        if created:
            print(f"✅ Компания создана: {company_data['name']}")

    # Создаем тестовые учебные заведения
    institutions_data = [
        {'name': 'МГТУ им. Баумана', 'email': 'practice@bmstu.ru', 'phone': '+7-495-777-77-77'},
        {'name': 'МИСиС', 'email': 'internship@misis.ru', 'phone': '+7-495-888-88-88'},
        {'name': 'МФТИ', 'email': 'career@phystech.edu', 'phone': '+7-495-999-99-99'},
        {'name': 'МИРЭА', 'email': 'career@mirea.edu', 'phone': '+7-495-999-89-89'},

    ]

    for inst_data in institutions_data:
        institution, created = EducationalInstitution.objects.get_or_create(
            name=inst_data['name'],
            defaults={
                'contact_email': inst_data['email'],
                'contact_phone': inst_data['phone']
            }
        )
        if created:
            print(f"✅ Учебное заведение создано: {inst_data['name']}")

    print("\n🎯 Начальные данные созданы успешно!")


if __name__ == '__main__':
    create_initial_data()