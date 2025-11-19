from django.db import models


class VacancyManager(models.Manager):
    def published(self):
        return self.filter(status='published')

    def for_company(self, company):
        return self.filter(company=company)

    def for_moderation(self):
        return self.filter(status='moderation')


class InternshipManager(models.Manager):
    def published(self):
        return self.filter(status='published')

    def for_moderation(self):
        return self.filter(status='moderation')