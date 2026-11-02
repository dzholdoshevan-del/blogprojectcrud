"""Служебная команда: печатает результаты тестов в JSON (её вызывает веб-страница
в отдельном процессе, чтобы не запускать тесты внутри работающего сервера)."""
import json

from django.core.management.base import BaseCommand

from reports.services import collect


class Command(BaseCommand):
    help = 'Печатает список и результаты тестов в формате JSON.'

    def add_arguments(self, parser):
        parser.add_argument('labels', nargs='*')
        parser.add_argument('--no-run', action='store_true')

    def handle(self, *args, **options):
        ctx = collect(options['labels'], run=not options['no_run'])
        self.stdout.write(json.dumps(ctx, ensure_ascii=True))
