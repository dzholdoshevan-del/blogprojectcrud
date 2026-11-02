from django.test import TestCase
from django.urls import reverse

from .models import Blog


class BlogListViewTests(TestCase):
    """Часть 1: тесты List (список статей)."""

    @classmethod
    def setUpTestData(cls):
        cls.blog1 = Blog.objects.create(title='Первая статья', content='Текст первой статьи')
        cls.blog2 = Blog.objects.create(title='Вторая статья', content='Текст второй статьи')
        cls.url = reverse('blog:list')

    # 1. Страница списка открывается
    def test_list_status_code_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    # 2. Используется правильный шаблон
    def test_list_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'blog/blog_list.html')

    # 3. На выходе получаем контент (заголовки статей есть на странице)
    def test_list_contains_content(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'Первая статья')
        self.assertContains(response, 'Вторая статья')

    # 4. В контексте есть все блоги
    def test_list_context_has_all_blogs(self):
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['blogs']), 2)

    # 5. Получаем ли id: в ссылках на странице есть pk каждого блога
    def test_list_contains_ids_in_links(self):
        response = self.client.get(self.url)
        self.assertContains(response, f'/blog/{self.blog1.pk}/')
        self.assertContains(response, f'/blog/{self.blog2.pk}/')

    # 6. Ссылки действительно ведут на детальные страницы
    def test_list_links_lead_to_detail_pages(self):
        response = self.client.get(self.url)
        for blog in (self.blog1, self.blog2):
            link = blog.get_absolute_url()
            self.assertContains(response, f'href="{link}"')
            detail = self.client.get(link)
            self.assertEqual(detail.status_code, 200)

    # 7. Пустой список: контента нет, показывается заглушка
    def test_list_empty(self):
        Blog.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['blogs']), 0)
        self.assertContains(response, 'Статей пока нет.')


class BlogDetailViewTests(TestCase):
    """Часть 1: тесты Detail (детальная страница)."""

    @classmethod
    def setUpTestData(cls):
        cls.blog = Blog.objects.create(title='Детальная статья', content='Полный текст статьи')

    # 1. Существующий id: страница открывается
    def test_detail_existing_id_returns_200(self):
        response = self.client.get(reverse('blog:detail', kwargs={'pk': self.blog.pk}))
        self.assertEqual(response.status_code, 200)

    # 2. Несуществующий id: 404
    def test_detail_nonexistent_id_returns_404(self):
        response = self.client.get(reverse('blog:detail', kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    # 3. Некорректный id (не число): 404, URL не совпадает с маршрутом
    def test_detail_invalid_id_returns_404(self):
        response = self.client.get('/blog/abc/')
        self.assertEqual(response.status_code, 404)

    # 4. Контент есть на странице
    def test_detail_contains_content(self):
        response = self.client.get(self.blog.get_absolute_url())
        self.assertContains(response, 'Детальная статья')
        self.assertContains(response, 'Полный текст статьи')

    # 5. В контексте именно нужный объект с нужным id
    def test_detail_context_has_correct_object(self):
        response = self.client.get(self.blog.get_absolute_url())
        self.assertEqual(response.context['blog'].pk, self.blog.pk)

    # 6. Правильный шаблон
    def test_detail_uses_correct_template(self):
        response = self.client.get(self.blog.get_absolute_url())
        self.assertTemplateUsed(response, 'blog/blog_detail.html')

    # 7. Ссылка «Назад» ведёт на список и действительно работает
    def test_detail_back_link_leads_to_list(self):
        response = self.client.get(self.blog.get_absolute_url())
        list_url = reverse('blog:list')
        self.assertContains(response, f'href="{list_url}"')
        self.assertEqual(self.client.get(list_url).status_code, 200)


class BlogLikesTests(TestCase):
    """Часть 2: счётчик лайков/просмотров."""

    # У нового блога количество лайков изначально равно нулю
    def test_new_blog_has_zero_likes(self):
        blog = Blog.objects.create(title='Новый блог', content='Текст')
        self.assertEqual(blog.likes, 0)

    # GET на детальную страницу увеличивает лайки на 1 (пока падает: логики нет)
    def test_detail_page_visit_increments_likes(self):
        blog = Blog.objects.create(title='Блог для лайков', content='Текст')
        response = self.client.get(reverse('blog:detail', kwargs={'pk': blog.pk}))
        self.assertEqual(response.status_code, 200)
        blog.refresh_from_db()
        self.assertEqual(blog.likes, 1)
