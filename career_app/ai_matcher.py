import re
from difflib import SequenceMatcher
from collections import Counter
import math
from .models import Applicant, Vacancy, IdealCandidateProfile, IdealVacancyProfile, AISearchMatch


class AIMatcher:

    @staticmethod
    def calculate_semantic_similarity(text1, text2):
        """Улучшенное вычисление смысловой схожести"""
        if not text1 or not text2:
            return 0

        text1 = text1.lower().strip()
        text2 = text2.lower().strip()

        # Если тексты очень похожи по заголовкам - повышаем оценку
        words1 = set(text1.split())
        words2 = set(text2.split())

        # Проверяем совпадение ключевых слов
        common_words = words1 & words2
        if common_words:
            word_similarity = len(common_words) / max(len(words1), len(words2)) * 100
        else:
            word_similarity = 0

        # Используем SequenceMatcher для общего сравнения
        sequence_similarity = SequenceMatcher(None, text1, text2).ratio() * 100

        # Комбинируем оба подхода
        final_similarity = max(word_similarity, sequence_similarity)

        # Повышаем оценку если есть точные совпадения ключевых слов
        key_terms = ['python', 'developer', 'разработчик', 'frontend', 'backend', 'javascript', 'react']
        for term in key_terms:
            if term in text1 and term in text2:
                final_similarity += 10  # Бонус за ключевые термины

        return min(int(final_similarity), 100)

    @staticmethod
    def extract_requirements(text):
        """Извлекает требования/навыки из текста автоматически"""
        if not text:
            return []

        text_lower = text.lower()
        requirements = []

        # Паттерны для извлечения требований
        patterns = [
            r'требования?[:\s]*([^.!?]+)[.!?]',
            r'навыки?[:\s]*([^.!?]+)[.!?]',
            r'умение[:\s]*([^.!?]+)[.!?]',
            r'обязанности?[:\s]*([^.!?]+)[.!?]',
            r'знание[:\s]*([^.!?]+)[.!?]',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                # Разбиваем на отдельные требования
                items = re.split(r'[,;]|\s+и\s+', match)
                requirements.extend([item.strip() for item in items if len(item.strip()) > 2])

        # Если не нашли по паттернам, берем все существительные и глаголы
        if not requirements:
            words = re.findall(r'\b[а-яa-z]{3,}\b', text_lower)
            # Фильтруем слишком общие слова
            general_words = {'работа', 'опыт', 'знание', 'умение', 'требование', 'навык'}
            requirements = [word for word in words if word not in general_words]

        return list(set(requirements))  # Убираем дубликаты

    @staticmethod
    def is_almost_empty_resume(text):
        """Проверяет, является ли резюме практически пустым"""
        if not text:
            return True

        # Убираем стандартные метки полей и проверяем реальный контент
        cleaned_text = re.sub(
            r'(Должность:|Уровень опыта:|Уровень образования:|Навыки:|Резюме:|Опыт:|Образование:|О себе:|Соискатель:)',
            '', text)
        cleaned_text = cleaned_text.strip()

        # Если после очистки осталось мало значимого текста
        meaningful_words = [word for word in cleaned_text.split() if len(word) > 2]
        return len(meaningful_words) < 5  # Меньше 5 значимых слов - считаем пустым

    @staticmethod
    def match_candidate_with_profile(applicant, ideal_profile):
        """Сопоставляет кандидата с идеальным профилем с улучшенной логикой"""
        applicant_text = applicant.get_full_resume_text()

        # Если резюме практически пустое, сильно снижаем оценку
        if AIMatcher.is_almost_empty_resume(applicant_text):
            return {
                'semantic_similarity': 0,
                'skills_match': 0,
                'experience_match': 0,
                'final_score': 0,
                'matched_concepts': [],
                'explanation': "Резюме слишком пустое для анализа"
            }

        # Смысловая схожесть
        semantic_similarity = AIMatcher.calculate_semantic_similarity(
            applicant_text,
            ideal_profile.ideal_resume
        )

        # Извлекаем и сравниваем требования
        applicant_skills = AIMatcher.extract_requirements(applicant_text)
        required_skills = AIMatcher.extract_requirements(
            ideal_profile.ideal_resume + " " + ideal_profile.required_skills
        )

        # Схожесть требований
        skills_match = AIMatcher.calculate_skills_match(applicant_skills, required_skills)

        # Опыт работы (определяем по контексту)
        experience_match = AIMatcher.match_experience_by_context(
            applicant_text,
            ideal_profile.experience_level
        )

        # Взвешенная оценка с акцентом на смысл
        final_score = int(
            semantic_similarity * 0.6 +  # Главное - смысловая схожесть
            skills_match * 0.3 +  # Конкретные требования
            experience_match * 0.1  # Уровень опыта
        )

        return {
            'semantic_similarity': semantic_similarity,
            'skills_match': skills_match,
            'experience_match': experience_match,
            'final_score': final_score,
            'matched_concepts': applicant_skills[:10],
            'explanation': AIMatcher.generate_explanation(
                semantic_similarity, skills_match, experience_match
            )
        }

    @staticmethod
    def calculate_skills_match(skills1, skills2):
        """Сравнивает наборы навыков"""
        if not skills2:
            return 100

        # Считаем схожесть каждого навыка с каждым
        total_match = 0

        for skill2 in skills2:
            best_match = 0
            for skill1 in skills1:
                similarity = SequenceMatcher(None, skill1, skill2).ratio()
                if similarity > best_match:
                    best_match = similarity

            total_match += best_match

        return int((total_match / len(skills2)) * 100)

    @staticmethod
    def match_experience_by_context(text, target_experience):
        """Определяет уровень опыта по контексту"""
        text_lower = text.lower()

        # Ключевые слова для разных уровней
        experience_keywords = {
            'junior': ['стажер', 'начинающий', 'младший', 'без опыта', 'учусь'],
            'middle': ['опыт', 'работал', 'разрабатывал', 'создавал', 'участвовал'],
            'senior': ['ведущий', 'старший', 'руководил', 'управлял', 'архитектура', 'стратеги'],
            'lead': ['тимлид', 'руководитель', 'управление', 'менеджер', 'координация']
        }

        # Считаем вес каждого уровня в тексте
        level_weights = {}
        for level, keywords in experience_keywords.items():
            weight = sum(1 for keyword in keywords if keyword in text_lower)
            level_weights[level] = weight

        # Определяем доминирующий уровень
        if not level_weights:
            return 0

        dominant_level = max(level_weights.items(), key=lambda x: x[1])[0]

        # Сравниваем с целевым уровнем
        if dominant_level == target_experience.lower():
            return 100

        # Получаем список уровней для сравнения позиций
        levels = list(experience_keywords.keys())
        try:
            dominant_index = levels.index(dominant_level)
            target_index = levels.index(target_experience.lower())
            level_diff = abs(dominant_index - target_index)

            if level_diff == 1:
                return 70  # Соседний уровень
            else:
                return 30  # Далекий уровень
        except ValueError:
            return 30  # Если уровень не найден

    @staticmethod
    def generate_explanation(semantic, skills, experience):
        """Генерирует понятное объяснение совпадения"""
        explanations = []

        if semantic > 80:
            explanations.append("Отличное смысловое соответствие")
        elif semantic > 60:
            explanations.append("Хорошее смысловое соответствие")
        elif semantic > 40:
            explanations.append("Умеренное смысловое соответствие")
        else:
            explanations.append("Слабое смысловое соответствие")

        if skills > 80:
            explanations.append("высокое совпадение требований")
        elif skills > 60:
            explanations.append("хорошее совпадение требований")

        if experience > 80:
            explanations.append("идеальное соответствие уровня опыта")

        return ". ".join(explanations)

    @staticmethod
    def find_candidates_for_hr(ideal_profile):
        """Умный поиск кандидатов с фильтрацией пустых резюме"""
        # Ищем только опубликованные резюме
        applicants = Applicant.objects.filter(is_published=True)
        matches = []

        print(f"\n=== ПОИСК КАНДИДАТОВ ДЛЯ: {ideal_profile.title} ===")
        print(f"Всего кандидатов в базе: {applicants.count()}")

        for applicant in applicants:
            # Проверяем, не пустое ли резюме
            resume_text = applicant.get_full_resume_text()
            if AIMatcher.is_almost_empty_resume(resume_text):
                print(f"❌ Пропускаем пустое резюме: {applicant.first_name} {applicant.last_name}")
                continue

            match_result = AIMatcher.match_candidate_with_profile(applicant, ideal_profile)

            print(f"Кандидат: {applicant.first_name} {applicant.last_name} - {match_result['final_score']}%")

            if match_result['final_score'] >= ideal_profile.min_match_percentage:
                matches.append({
                    'applicant': applicant,
                    'match_details': match_result,
                    'score': match_result['final_score']
                })
                print(f"✅ ДОБАВЛЕН: {applicant.first_name} {applicant.last_name}")

        print(f"Найдено подходящих кандидатов: {len(matches)}")

        # Сортируем по смыслу
        matches.sort(key=lambda x: x['match_details']['semantic_similarity'], reverse=True)
        top_matches = matches[:ideal_profile.max_candidates]

        # Удаляем старые совпадения
        AISearchMatch.objects.filter(ideal_candidate_profile=ideal_profile).delete()

        # Сохраняем новые результаты
        for match in top_matches:
            AISearchMatch.objects.create(
                ideal_candidate_profile=ideal_profile,
                matched_applicant=match['applicant'],
                match_percentage=match['score'],
                match_details=match['match_details']
            )

        return top_matches

    @staticmethod
    def find_vacancies_for_applicant(ideal_profile):
        """Умный поиск вакансий с улучшенным алгоритмом"""
        vacancies = Vacancy.objects.filter(status='published')
        matches = []

        print(f"\n=== УЛУЧШЕННЫЙ ПОИСК ВАКАНСИЙ ===")

        # Используем правильные поля из модели IdealVacancyProfile
        profile_title = getattr(ideal_profile, 'title', '')
        desired_skills = getattr(ideal_profile, 'desired_skills', '')
        tech_stack = getattr(ideal_profile, 'tech_stack', '')

        # Формируем идеальный запрос из всех доступных полей
        ideal_text = f"{profile_title} {desired_skills} {tech_stack}"

        print(f"Поиск для: {profile_title}")
        print(f"Минимальный %: {ideal_profile.min_match_percentage}")
        print(f"Всего вакансий: {vacancies.count()}")

        for vacancy in vacancies:
            vacancy_text = f"{vacancy.title} {vacancy.description} {vacancy.requirements}"

            similarity = AIMatcher.calculate_semantic_similarity(vacancy_text, ideal_text)

            print(f"'{vacancy.title}' - {similarity}%")

            if similarity >= ideal_profile.min_match_percentage:
                matches.append({
                    'vacancy': vacancy,
                    'match_details': {
                        'semantic_similarity': similarity,
                        'final_score': similarity,
                        'explanation': f"Смысловое соответствие: {similarity}%"
                    },
                    'score': similarity
                })

        print(f"Найдено совпадений: {len(matches)}")

        # Удаляем старые совпадения для этого профиля
        AISearchMatch.objects.filter(ideal_vacancy_profile=ideal_profile).delete()

        # Сохраняем новые результаты
        for match in matches:
            AISearchMatch.objects.create(
                ideal_vacancy_profile=ideal_profile,
                matched_vacancy=match['vacancy'],
                match_percentage=match['score'],
                match_details=match['match_details']
            )

        return matches