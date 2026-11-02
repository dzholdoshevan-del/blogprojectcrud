"""python manage.py export_tests_docx [приложение ...] [-o файл.docx] [--no-run]"""
from django.core.management.base import BaseCommand

from reports.docx_builder import build_docx
from reports.services import collect


class Command(BaseCommand):
    help = 'Запускает все тесты проекта и записывает их в Word-файл.'

    def add_arguments(self, parser):
        parser.add_argument('labels', nargs='*')
        parser.add_argument('--output', '-o', default='test_report.docx')
        parser.add_argument('--no-run', action='store_true', help='Не запускать тесты.')

    def handle(self, *args, **options):
        ctx = collect(options['labels'], run=not options['no_run'])
        build_docx(ctx, options['output'])
        self.stdout.write(self.style.SUCCESS(f"Готово: {ctx['total']} тестов записано в {options['output']}"))
