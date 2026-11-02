from django.db import models
from django.urls import reverse


class Item(models.Model):
    """Шаблонная модель для CRUD.
    На лабораторной переименуйте её (например, в Product, Book, Task)
    и замените поля на нужные по заданию."""

    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('crud:detail', kwargs={'pk': self.pk})
