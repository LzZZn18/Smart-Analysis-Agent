# -*- coding: utf-8 -*-
"""docx 生成辅助库：对齐第21组模板风格。
标题居中/章节编号/正文/表格/签名页 统一封装。
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn


def new_doc():
    """创建文档并设置默认中文字体。"""
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "宋体"
    style.font.size = Pt(11)
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    return doc


def _set_font(run, size=11, bold=False, name="宋体", east="宋体", color=None, italic=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    r = run._element.rPr.rFonts
    r.set(qn("w:eastAsia"), east)
    if color:
        run.font.color.rgb = RGBColor(*color)


def doc_title(doc, text, size=20):
    """文档主标题：居中、加粗。"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    _set_font(r, size=size, bold=True, name="黑体", east="黑体")
    p.paragraph_format.space_after = Pt(6)
    return p


def doc_subtitle(doc, text, size=12):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    _set_font(r, size=size, bold=False)
    return p


def h1(doc, text, size=15):
    """一级标题：一、xxx"""
    p = doc.add_paragraph()
    r = p.add_run(text)
    _set_font(r, size=size, bold=True, name="黑体", east="黑体")
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    return p


def h2(doc, text, size=13):
    """二级标题：（一）xxx / 1. xxx"""
    p = doc.add_paragraph()
    r = p.add_run(text)
    _set_font(r, size=size, bold=True)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    return p


def para(doc, text, size=11, bold=False, indent=0):
    """普通段落。"""
    p = doc.add_paragraph()
    r = p.add_run(text)
    _set_font(r, size=size, bold=bold)
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    p.paragraph_format.line_spacing = 1.4
    return p


def bullet(doc, text, size=11):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(text)
    _set_font(r, size=size)
    return p


def number_list(doc, items, size=11):
    """带序号列表。"""
    for i, it in enumerate(items, 1):
        p = doc.add_paragraph()
        r = p.add_run(it)
        _set_font(r, size=size)


def table(doc, headers, rows, style="Table Grid"):
    """通用表格。"""
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = style
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(headers):
        cell = t.rows[0].cells[j]
        cell.text = ""
        r = cell.paragraphs[0].add_run(h)
        _set_font(r, size=10, bold=True)
    for row in rows:
        cells = t.add_row().cells
        for j, val in enumerate(row):
            cells[j].text = ""
            r = cells[j].paragraphs[0].add_run(str(val))
            _set_font(r, size=10)
    return t


def cover_table(doc, content_rows):
    """封面信息表格：content_rows 为二维行列表，每行若干"标签,值"单元格。

    例如 [["项目名称","...","组别","XX"]] 会渲染成一行的 4 个单元格。
    """
    # 推断最大列数
    ncols = max(len(r) for r in content_rows)
    t = doc.add_table(rows=0, cols=ncols)
    t.style = "Table Grid"
    for row in content_rows:
        cells = t.add_row().cells
        for j, val in enumerate(row):
            cells[j].text = ""
            r = cells[j].paragraphs[0].add_run(str(val))
            _set_font(r, size=10, bold=(j % 2 == 0))  # 标签列加粗
    return t


def sign_table(doc, headers, rows):
    """签名页表格（全组电子签名）。"""
    return table(doc, headers, rows)
