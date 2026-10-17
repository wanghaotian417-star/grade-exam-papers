"""Shared status definitions, JSON I/O and optional image/PDF dependencies."""
import json
import math
from pathlib import Path

STATUSES = {'correct', 'partial', 'incorrect', 'unanswered', 'pending', 'not_provided'}
RUBRICS = {'none', 'user', 'official', 'suggested'}
DECIDED = {'correct', 'partial', 'incorrect', 'unanswered'}
LABELS = {'correct': '正确', 'partial': '部分正确', 'incorrect': '错误',
          'unanswered': '确认空白', 'pending': '待确认', 'not_provided': '未提供'}
COLORS = {'correct': '#14804a', 'partial': '#b76600', 'incorrect': '#cc2833',
          'unanswered': '#cc2833', 'pending': '#2265b0', 'not_provided': '#2265b0'}
TAGS = {'correct': 'OK', 'partial': 'PART', 'incorrect': 'X',
        'unanswered': 'BLANK', 'pending': '?', 'not_provided': '?'}

def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def save_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2,
                                    allow_nan=False) + '\n', encoding='utf-8')


def get_pillow():
    try:
        from PIL import Image, ImageDraw, ImageOps
        return Image, ImageDraw, ImageOps
    except ImportError as exc:
        raise ValueError('需要Pillow；请使用已有图片工具或安装pillow。') from exc


def get_fitz():
    try:
        import fitz
        return fitz
    except ImportError as exc:
        raise ValueError('PDF处理需要PyMuPDF；请使用已有PDF工具或安装pymupdf。') from exc


def rgb(image):
    Image, _, ImageOps = get_pillow()
    image = ImageOps.exif_transpose(image)
    if image.mode in ('RGBA', 'LA') or 'transparency' in image.info:
        rgba = image.convert('RGBA')
        background = Image.new('RGBA', rgba.size, 'white')
        background.alpha_composite(rgba)
        return background.convert('RGB')
    return image.convert('RGB')
