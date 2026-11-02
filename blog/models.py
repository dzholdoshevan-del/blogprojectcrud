from django.db import models
from django.urls import reverse


class Blog(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    content = models.TextField('Содержание')
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    # Счётчик лайков/просмотров, по умолчанию 0
    likes = models.PositiveIntegerField('Лайки', default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:detail', kwargs={'pk': self.pk})
