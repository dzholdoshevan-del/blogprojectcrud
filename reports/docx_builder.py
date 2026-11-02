"""Сборка настоящего .docx из контекста (python-docx)."""
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

FONT = 'Times New Roman'
GREEN, RED, GREY = 'C6EFCE', 'FFC7CE', 'D9D9D9'


def set_font(run, size=12, bold=False, italic=False, name=FONT, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    run.font.size = Pt(size)
    run.bold, run.italic = bold, italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def shade(element, fill):
    pr = element.get_or_add_tcPr() if hasattr(element, 'get_or_add_tcPr') else element.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    pr.append(shd)


def para(doc, text='', size=12, bold=False, italic=False, align=None, after=6):
    p = doc.add_paragraph()
    if align:
        p.alignment = align
    p.paragraph_format.space_after = Pt(after)
    set_font(p.add_run(text), size, bold, italic)
    return p


def heading(doc, text, level):
    h = doc.add_heading(level=level)
    set_font(h.add_run(text), {1: 16, 2: 14, 3: 12}[level], bold=True, color='000000')


def code_block(doc, text, size=9):
    for line in text.split('\n'):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        shade(p._p, 'F2F2F2')
        set_font(p.add_run(line or ' '), size, name='Courier New')
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def cell_text(cell, text, bold=False, size=11, fill=None, center=False):
    cell.text = ''
    p = cell.paragraphs[0]
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run(text), size, bold)
    if fill:
        shade(cell._tc, fill)


def build_docx(ctx, target):
    """target — путь к файлу или файловый объект (BytesIO / HttpResponse)."""
    doc = Document()
    doc.styles['Normal'].font.name = FONT
    doc.styles['Normal'].font.size = Pt(12)

    para(doc, 'ОТЧЁТ О ТЕСТИРОВАНИИ DJANGO-ПРОЕКТА', 18, True, align=WD_ALIGN_PARAGRAPH.CENTER, after=4)
    para(doc, f"Сформирован: {ctx['generated']}", 12, align=WD_ALIGN_PARAGRAPH.CENTER, after=14)

    heading(doc, '1. Общая сводка', 1)
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell_text(table.rows[0].cells[0], 'Показатель', True, fill=GREY)
    cell_text(table.rows[0].cells[1], 'Значение', True, fill=GREY)
    rows = [('Всего тестов', ctx['total']), ('Тестовых классов', len(ctx['groups']))]
    if ctx['ran']:
        rows += [('Пройдено', ctx['passed']), ('Упало / с ошибкой', ctx['failed_count'])]
    for k, v in rows:
        r = table.add_row().cells
        cell_text(r[0], k)
        cell_text(r[1], str(v), center=True)
    para(doc, '', after=6)

    heading(doc, '2. Список тестов по классам', 1)
    widths = [0.4, 2.6, 2.6, 0.9]
    for n, g in enumerate(ctx['groups'], 1):
        heading(doc, f"2.{n}. {g['cls']}  ({g['module']})", 2)
        if g['doc']:
            para(doc, g['doc'], 12, italic=True)
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Table Grid'
        for i, h in enumerate(['№', 'Тест', 'Что проверяется', 'Результат']):
            cell_text(table.rows[0].cells[i], h, True, fill=GREY)
        for t in g['tests']:
            fill = GREEN if t['status'] == 'OK' else RED if t['status'] in ('FAIL', 'ERROR') else None
            row = table.add_row().cells
            cell_text(row[0], str(t['num']), center=True)
            cell_text(row[1], t['name'], size=10)
            cell_text(row[2], t['description'] or '—', size=10)
            cell_text(row[3], t['status_ru'], True, fill=fill, center=True)
        table.autofit = False
        for col, w in zip(table.columns, widths):
            col.width = Pt(w * 72)
        for row in table.rows:
            for c, w in zip(row.cells, widths):
                c.width = Pt(w * 72)
        para(doc, '', after=6)

    heading(doc, '3. Исходный код тестов', 1)
    for n, g in enumerate(ctx['groups'], 1):
        heading(doc, f"3.{n}. {g['cls']}", 2)
        for t in g['tests']:
            para(doc, t['name'], 12, True, after=2)
            if t['source']:
                code_block(doc, t['source'])

    if ctx['failed']:
        heading(doc, '4. Упавшие тесты (подробности)', 1)
        for t in ctx['failed']:
            para(doc, f"{t['module']}.{t['cls']}.{t['name']}", 12, True, after=2)
            code_block(doc, t['error'])

    doc.save(target)
