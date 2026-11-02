"""Сбор всех тестов проекта: название, описание, исходный код, результат."""
import inspect
import io
import textwrap
import unittest
from datetime import datetime
from pathlib import Path

from django.test.runner import DiscoverRunner

STATUS_RU = {'OK': 'Пройден', 'FAIL': 'Упал', 'ERROR': 'Ошибка', '—': '—'}


def iter_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_tests(item)
        else:
            yield item


def describe(test):
    """(описание, исходный код). Описание = docstring или комментарии над def."""
    method = getattr(test, getattr(test, '_testMethodName', ''), None)
    func = getattr(method, '__func__', method)
    if func is None:
        return '', ''
    try:
        lines, start = inspect.getsourcelines(func)
        source = textwrap.dedent(''.join(lines)).rstrip()
        file_lines = Path(inspect.getsourcefile(func)).read_text(encoding='utf-8').splitlines()
    except (OSError, TypeError):
        return inspect.getdoc(func) or '', ''
    comments, i = [], start - 2
    while i >= 0 and file_lines[i].strip().startswith('#'):
        comments.insert(0, file_lines[i].strip().lstrip('#').strip())
        i -= 1
    return inspect.getdoc(func) or ' '.join(comments), source


class Collector(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = {}

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records[test.id()] = ('OK', '')

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records[test.id()] = ('FAIL', self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self.records[test.id()] = ('ERROR', self._exc_info_to_string(err, test))


def collect(labels=None, run=True):
    """Находит тесты проекта, (по желанию) запускает их и возвращает
    готовый контекст для шаблона Django / сборщика docx."""
    runner = DiscoverRunner(verbosity=0, interactive=False)
    runner.setup_test_environment()
    suite = runner.build_suite(list(labels) if labels else None)
    tests = list(iter_tests(suite))

    results = {}
    if run:
        old_config = runner.setup_databases()
        try:
            results = unittest.TextTestRunner(
                stream=io.StringIO(), verbosity=0, resultclass=Collector).run(suite).records
        finally:
            runner.teardown_databases(old_config)
    runner.teardown_test_environment()

    records = []
    for t in tests:
        desc, src = describe(t)
        status, error = results.get(t.id(), ('—', ''))
        records.append({
            'module': t.__class__.__module__,
            'cls': t.__class__.__name__,
            'cls_doc': (inspect.getdoc(t.__class__) or '') if not (inspect.getdoc(t.__class__) or '').startswith('A class whose') else '',
            'name': getattr(t, '_testMethodName', t.id()),
            'description': desc,
            'source': src,
            'status': status,
            'status_ru': STATUS_RU[status],
            'error': error.strip(),
        })
    return build_context(records, ran=run)


def build_context(records, ran):
    groups = {}
    for r in records:
        g = groups.setdefault((r['module'], r['cls']),
                              {'module': r['module'], 'cls': r['cls'], 'doc': r['cls_doc'], 'tests': []})
        r['num'] = len(g['tests']) + 1
        g['tests'].append(r)
    failed = [r for r in records if r['status'] in ('FAIL', 'ERROR')]
    return {
        'generated': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'ran': ran,
        'total': len(records),
        'passed': sum(1 for r in records if r['status'] == 'OK'),
        'failed_count': len(failed),
        'failed': failed,
        'groups': list(groups.values()),
    }
