import json
import os
import subprocess
import sys
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from .docx_builder import build_docx


def get_context(request):
    """Запускает тесты в отдельном процессе и возвращает контекст для шаблона.
    ?run=0 — не запускать тесты, показать только список и код."""
    cmd = [sys.executable, str(settings.BASE_DIR / 'manage.py'), 'export_tests_json']
    if request.GET.get('run') == '0':
        cmd.append('--no-run')
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                          cwd=settings.BASE_DIR, timeout=300,
                          env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
    ctx = json.loads(proc.stdout)
    ctx['run_flag'] = '0' if request.GET.get('run') == '0' else '1'
    return ctx


def report_page(request):
    """Страница с отчётом (оформление — Django-шаблон)."""
    return render(request, 'reports/report.html', get_context(request))


def download_doc(request):
    """Word-файл, оформленный Django-шаблоном (HTML, который открывает Word)."""
    html = render_to_string('reports/report_word.html', get_context(request), request)
    response = HttpResponse(html, content_type='application/msword; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="test_report.doc"'
    return response


def download_docx(request):
    """Настоящий .docx (собирается python-docx)."""
    buffer = BytesIO()
    build_docx(get_context(request), buffer)
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = 'attachment; filename="test_report.docx"'
    return response
