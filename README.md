# Django-проект: blog + crud + reports

    pip install -r requirements.txt
    python manage.py migrate
    python manage.py test                       # blog: 1 тест падает намеренно (лайки)
    python manage.py runserver

## Адреса
- /                       — блог (List/Detail)
- /items/                 — CRUD
- /reports/               — отчёт по ВСЕМ тестам проекта (оформлен Django-шаблоном)
- /reports/download.doc   — скачать Word (.doc), оформление: шаблон reports/report_word.html
- /reports/download.docx  — скачать Word (.docx), собирается python-docx
- /reports/?run=0         — показать только список и код, без запуска тестов

## Как это работает (для защиты)
1. reports/services.py — находит все тесты проекта (DiscoverRunner), берёт имя, описание
   (комментарий над тестом), исходный код (inspect) и запускает их, собирая результат.
2. reports/views.py — view запускает сбор в отдельном процессе (manage.py export_tests_json),
   получает JSON и передаёт его в шаблон.
3. reports/templates/reports/report.html — страница в браузере.
   reports/templates/reports/report_word.html — тот же отчёт для Word: view отдаёт его
   с content_type 'application/msword' и заголовком Content-Disposition: attachment,
   поэтому браузер скачивает файл, а Word его открывает.
4. Из консоли: python manage.py export_tests_docx -o otchet.docx

## Тесты CRUD (crud/tests.py, 47 тестов)
    python manage.py test crud                          # только CRUD
    python manage.py export_tests_docx crud -o crud.docx  # Word-отчёт только по CRUD
Покрыто: модель (8), форма (6), адреса (3), CREATE (6), READ (10), UPDATE (6), DELETE (7), сквозной цикл (1).

## Приложения
- blog    — List/Detail, поле likes, тесты (лаба 1)
- crud    — готовый CRUD-шаблон (Item): list, detail, create, update, delete + 13 тестов
- reports — отчёт по тестам -> Word

## Как использовать crud на следующей лабе
1. crud/models.py: переименуйте Item (например, в Product) и замените поля по заданию.
2. crud/forms.py: в fields перечислите те же поля.
3. Замените Item -> Product в views.py, admin.py, tests.py, шаблонах (поиск и замена по проекту).
4. Удалите crud/migrations/0001_initial.py и db.sqlite3, затем:
       python manage.py makemigrations
       python manage.py migrate
5. python manage.py test — все тесты должны пройти, затем откройте /reports/ и скачайте Word.

## Чтобы тест лайков прошёл (blog/views.py)
    from django.db.models import F
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        Blog.objects.filter(pk=obj.pk).update(likes=F('likes') + 1)
        obj.refresh_from_db()
        return obj
