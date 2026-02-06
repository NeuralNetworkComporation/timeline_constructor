from django.db import models


class BoardConnection(models.Model):
    source = models.ForeignKey(
        'BoardTimeline',
        on_delete=models.CASCADE,
        related_name='outgoing_connections',
        verbose_name="Источник"
    )
    target = models.ForeignKey(
        'BoardTimeline',
        on_delete=models.CASCADE,
        related_name='incoming_connections',
        verbose_name="Цель"
    )

    label = models.CharField(max_length=100, blank=True, verbose_name="Метка")
    color = models.CharField(max_length=20, default='#3b82f6', verbose_name="Цвет линии")
    line_style = models.CharField(
        max_length=20,
        default='solid',
        choices=[('solid', 'Сплошная'), ('dashed', 'Пунктир'), ('dotted', 'Точки')],
        verbose_name="Стиль линии"
    )
    arrow_type = models.CharField(
        max_length=20,
        default='arrow',
        choices=[('none', 'Без стрелки'), ('arrow', 'Стрелка'), ('circle', 'Круг')],
        verbose_name="Тип стрелки"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Соединение на доске"
        verbose_name_plural = "Соединения на доске"
        unique_together = ['source', 'target']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.source.title} → {self.target.title}"