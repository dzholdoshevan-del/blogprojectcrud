from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import resolve, reverse
from django.utils import timezone

from . import views
from .forms import ItemForm
from .models import Item


# =====================================================================
# 1. МОДЕЛЬ
# =====================================================================
class ItemModelTests(TestCase):
    """Модель Item"""

    # Строковое представление модели возвращает название
    def test_str_returns_title(self):
        item = Item.objects.create(title='Заметка')
        self.assertEqual(str(item), 'Заметка')

    # Описание необязательное: запись без описания проходит валидацию
    def test_description_is_optional(self):
        item = Item(title='Без описания')
        item.full_clean()
        self.assertEqual(item.description, '')

    # Название обязательное: пустое название не проходит валидацию
    def test_title_is_required(self):
        with self.assertRaises(ValidationError):
            Item(title='').full_clean()

    # Название не длиннее 200 символов: 200 допустимо, 201 нет
    def test_title_max_length(self):
        Item(title='а' * 200).full_clean()
        with self.assertRaises(ValidationError):
            Item(title='а' * 201).full_clean()

    # Дата создания проставляется автоматически
    def test_created_at_is_set_automatically(self):
        item = Item.objects.create(title='Дата')
        self.assertIsNotNone(item.created_at)

    # Дата обновления меняется при сохранении, дата создания остаётся прежней
    def test_updated_at_changes_on_save(self):
        item = Item.objects.create(title='Старое')
        created, updated = item.created_at, item.updated_at
        item.title = 'Новое'
        item.save()
        item.refresh_from_db()
        self.assertEqual(item.created_at, created)
        self.assertGreater(item.updated_at, updated)

    # get_absolute_url ведёт на страницу детали записи
    def test_get_absolute_url(self):
        item = Item.objects.create(title='Ссылка')
        self.assertEqual(item.get_absolute_url(), f'/items/{item.pk}/')

    # Записи упорядочены от новых к старым
    def test_default_ordering_newest_first(self):
        old = Item.objects.create(title='Старая')
        new = Item.objects.create(title='Новая')
        Item.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=1))
        self.assertEqual(list(Item.objects.all()), [new, old])


# =====================================================================
# 2. ФОРМА
# =====================================================================
class ItemFormTests(TestCase):
    """Форма ItemForm"""

    # Форма с корректными данными валидна
    def test_form_valid(self):
        form = ItemForm({'title': 'Название', 'description': 'Текст'})
        self.assertTrue(form.is_valid())

    # Пустое название: форма невалидна, ошибка в поле title
    def test_form_empty_title_invalid(self):
        form = ItemForm({'title': '', 'description': 'Текст'})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    # Слишком длинное название: форма невалидна
    def test_form_too_long_title_invalid(self):
        form = ItemForm({'title': 'а' * 201})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    # Описание можно не заполнять
    def test_form_description_optional(self):
        form = ItemForm({'title': 'Только название'})
        self.assertTrue(form.is_valid())

    # В форме только поля title и description
    def test_form_fields(self):
        self.assertEqual(list(ItemForm().fields), ['title', 'description'])

    # Валидная форма сохраняет запись в базу
    def test_form_save_creates_item(self):
        form = ItemForm({'title': 'Сохранить', 'description': 'Текст'})
        item = form.save()
        self.assertTrue(Item.objects.filter(pk=item.pk).exists())


# =====================================================================
# 3. АДРЕСА (URL)
# =====================================================================
class ItemUrlTests(TestCase):
    """Маршруты приложения crud"""

    # reverse() даёт ожидаемые адреса всех пяти страниц
    def test_reverse_urls(self):
        self.assertEqual(reverse('crud:list'), '/items/')
        self.assertEqual(reverse('crud:create'), '/items/create/')
        self.assertEqual(reverse('crud:detail', kwargs={'pk': 1}), '/items/1/')
        self.assertEqual(reverse('crud:update', kwargs={'pk': 1}), '/items/1/update/')
        self.assertEqual(reverse('crud:delete', kwargs={'pk': 1}), '/items/1/delete/')

    # Каждый адрес связан с нужным представлением
    def test_urls_resolve_to_views(self):
        self.assertEqual(resolve('/items/').func.view_class, views.ItemListView)
        self.assertEqual(resolve('/items/create/').func.view_class, views.ItemCreateView)
        self.assertEqual(resolve('/items/1/').func.view_class, views.ItemDetailView)
        self.assertEqual(resolve('/items/1/update/').func.view_class, views.ItemUpdateView)
        self.assertEqual(resolve('/items/1/delete/').func.view_class, views.ItemDeleteView)

    # Некорректный id в адресе (не число) даёт 404
    def test_invalid_pk_in_url_returns_404(self):
        self.assertEqual(self.client.get('/items/abc/').status_code, 404)
        self.assertEqual(self.client.get('/items/abc/update/').status_code, 404)
        self.assertEqual(self.client.get('/items/abc/delete/').status_code, 404)


# =====================================================================
# 4. CREATE
# =====================================================================
class ItemCreateTests(TestCase):
    """CREATE: создание записи"""

    # Страница формы создания открывается и использует нужный шаблон
    def test_create_page_opens(self):
        response = self.client.get(reverse('crud:create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/item_form.html')

    # На странице создания есть форма и csrf-токен
    def test_create_page_has_form_and_csrf(self):
        response = self.client.get(reverse('crud:create'))
        self.assertIsInstance(response.context['form'], ItemForm)
        self.assertContains(response, 'csrfmiddlewaretoken')

    # POST с корректными данными создаёт запись и делает редирект на деталь
    def test_create_valid_data(self):
        response = self.client.post(reverse('crud:create'),
                                    {'title': 'Новая', 'description': 'Текст'})
        self.assertEqual(Item.objects.count(), 1)
        item = Item.objects.get()
        self.assertEqual((item.title, item.description), ('Новая', 'Текст'))
        self.assertRedirects(response, item.get_absolute_url())

    # Запись можно создать только с названием, без описания
    def test_create_only_title(self):
        self.client.post(reverse('crud:create'), {'title': 'Одно название'})
        self.assertEqual(Item.objects.get().description, '')

    # POST с пустым названием не создаёт запись, форма показывает ошибку
    def test_create_invalid_data(self):
        response = self.client.post(reverse('crud:create'), {'title': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Item.objects.count(), 0)
        self.assertTrue(response.context['form'].errors)

    # POST без csrf-токена запрещён (403), запись не создаётся
    def test_create_without_csrf_forbidden(self):
        strict = Client(enforce_csrf_checks=True)
        response = strict.post(reverse('crud:create'), {'title': 'Взлом'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Item.objects.count(), 0)


# =====================================================================
# 5. READ
# =====================================================================
class ItemReadTests(TestCase):
    """READ: список и деталь"""

    @classmethod
    def setUpTestData(cls):
        cls.item = Item.objects.create(title='Запись 1', description='Описание 1')

    # Список открывается, шаблон верный, запись видна
    def test_list_contains_item(self):
        response = self.client.get(reverse('crud:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/item_list.html')
        self.assertContains(response, 'Запись 1')

    # Пустой список показывает заглушку
    def test_list_empty(self):
        Item.objects.all().delete()
        response = self.client.get(reverse('crud:list'))
        self.assertEqual(len(response.context['items']), 0)
        self.assertContains(response, 'Записей пока нет.')

    # В списке отображаются все записи
    def test_list_shows_all_items(self):
        Item.objects.create(title='Запись 2')
        Item.objects.create(title='Запись 3')
        response = self.client.get(reverse('crud:list'))
        self.assertEqual(len(response.context['items']), 3)

    # В списке есть ссылки на деталь, изменение, удаление и создание
    def test_list_has_action_links(self):
        response = self.client.get(reverse('crud:list'))
        self.assertContains(response, f'/items/{self.item.pk}/')
        self.assertContains(response, f'/items/{self.item.pk}/update/')
        self.assertContains(response, f'/items/{self.item.pk}/delete/')
        self.assertContains(response, reverse('crud:create'))

    # Ссылка из списка действительно открывает деталь
    def test_list_link_opens_detail(self):
        response = self.client.get(self.item.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    # Деталь существующей записи открывается и показывает данные
    def test_detail_existing(self):
        response = self.client.get(self.item.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/item_detail.html')
        self.assertContains(response, 'Запись 1')
        self.assertContains(response, 'Описание 1')

    # В контексте детали лежит нужный объект
    def test_detail_context_object(self):
        response = self.client.get(self.item.get_absolute_url())
        self.assertEqual(response.context['item'], self.item)

    # На детальной странице есть ссылки «Изменить», «Удалить» и «К списку»
    def test_detail_has_action_links(self):
        response = self.client.get(self.item.get_absolute_url())
        self.assertContains(response, f'/items/{self.item.pk}/update/')
        self.assertContains(response, f'/items/{self.item.pk}/delete/')
        self.assertContains(response, reverse('crud:list'))

    # Деталь несуществующей записи даёт 404
    def test_detail_not_found(self):
        response = self.client.get(reverse('crud:detail', kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    # POST на страницу детали не разрешён (405)
    def test_detail_post_not_allowed(self):
        response = self.client.post(self.item.get_absolute_url())
        self.assertEqual(response.status_code, 405)


# =====================================================================
# 6. UPDATE
# =====================================================================
class ItemUpdateTests(TestCase):
    """UPDATE: изменение записи"""

    @classmethod
    def setUpTestData(cls):
        cls.item = Item.objects.create(title='Старое', description='Текст')
        cls.url = reverse('crud:update', kwargs={'pk': cls.item.pk})

    # Форма редактирования открывается и содержит старые данные
    def test_update_page_prefilled(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/item_form.html')
        self.assertContains(response, 'Старое')

    # В форме редактирования передан именно нужный объект
    def test_update_context_object(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context['object'], self.item)

    # POST меняет данные в базе и ведёт на деталь
    def test_update_changes_data(self):
        response = self.client.post(self.url, {'title': 'Новое', 'description': 'Другой текст'})
        self.assertRedirects(response, self.item.get_absolute_url())
        self.item.refresh_from_db()
        self.assertEqual((self.item.title, self.item.description), ('Новое', 'Другой текст'))

    # После изменения количество записей не меняется (запись не дублируется)
    def test_update_does_not_create_new_item(self):
        self.client.post(self.url, {'title': 'Новое'})
        self.assertEqual(Item.objects.count(), 1)

    # Некорректные данные не меняют запись, форма показывает ошибку
    def test_update_invalid_data_keeps_old(self):
        response = self.client.post(self.url, {'title': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, 'Старое')

    # Редактирование несуществующей записи даёт 404 (и GET, и POST)
    def test_update_not_found(self):
        url = reverse('crud:update', kwargs={'pk': 9999})
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {'title': 'X'}).status_code, 404)


# =====================================================================
# 7. DELETE
# =====================================================================
class ItemDeleteTests(TestCase):
    """DELETE: удаление записи"""

    def setUp(self):
        self.item = Item.objects.create(title='Удаляемая')
        self.other = Item.objects.create(title='Остаётся')
        self.url = reverse('crud:delete', kwargs={'pk': self.item.pk})

    # Страница подтверждения удаления открывается и показывает название
    def test_delete_page_opens(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/item_confirm_delete.html')
        self.assertContains(response, 'Удаляемая')

    # GET-запрос ничего не удаляет (нужно подтверждение через POST)
    def test_delete_get_does_not_delete(self):
        self.client.get(self.url)
        self.assertTrue(Item.objects.filter(pk=self.item.pk).exists())

    # POST удаляет запись и ведёт на список
    def test_delete_removes_item(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('crud:list'))
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())

    # Удаляется только выбранная запись, остальные остаются
    def test_delete_only_selected(self):
        self.client.post(self.url)
        self.assertEqual(Item.objects.count(), 1)
        self.assertTrue(Item.objects.filter(pk=self.other.pk).exists())

    # После удаления страница детали даёт 404
    def test_detail_after_delete_returns_404(self):
        self.client.post(self.url)
        self.assertEqual(self.client.get(self.item.get_absolute_url()).status_code, 404)

    # Повторное удаление уже удалённой записи даёт 404
    def test_delete_twice_returns_404(self):
        self.client.post(self.url)
        self.assertEqual(self.client.post(self.url).status_code, 404)

    # Удаление несуществующей записи даёт 404
    def test_delete_not_found(self):
        response = self.client.post(reverse('crud:delete', kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)


# =====================================================================
# 8. СКВОЗНОЙ СЦЕНАРИЙ
# =====================================================================
class ItemCrudFlowTests(TestCase):
    """Полный цикл: создать, прочитать, изменить, удалить"""

    # Весь путь пользователя через тестовый клиент (follow=True идёт по редиректам)
    def test_full_crud_cycle(self):
        # CREATE
        response = self.client.post(reverse('crud:create'),
                                    {'title': 'Цикл', 'description': 'Первый вариант'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Первый вариант')
        item = Item.objects.get()

        # READ (список)
        self.assertContains(self.client.get(reverse('crud:list')), 'Цикл')

        # UPDATE
        response = self.client.post(reverse('crud:update', kwargs={'pk': item.pk}),
                                    {'title': 'Цикл', 'description': 'Второй вариант'}, follow=True)
        self.assertContains(response, 'Второй вариант')
        self.assertNotContains(response, 'Первый вариант')

        # DELETE
        response = self.client.post(reverse('crud:delete', kwargs={'pk': item.pk}), follow=True)
        self.assertContains(response, 'Записей пока нет.')
        self.assertEqual(Item.objects.count(), 0)
