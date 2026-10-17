"""Render full pages and retain original source/page mapping."""
import io
from pathlib import Path
from .common import get_pillow, get_fitz, rgb, save_json

def prepare(inputs, out, dpi):
    if not 72 <= dpi <= 300:
        raise ValueError('dpi须为72至300。')
    Image, _, _ = get_pillow()
    out = Path(out).resolve()
    sources = [Path(p).resolve() for p in inputs]
    if any(not p.is_file() for p in sources):
        raise ValueError('一个或多个输入文件不存在。')
    # Refuse to reuse a populated directory, avoiding accidental source/output overwrites.
    if out.exists() and any(out.iterdir()):
        raise ValueError('输出目录非空；请选择新的页面目录。')
    out.mkdir(parents=True, exist_ok=True)
    pages = []

    def emit(image, source, source_page):
        page_id = f'p{len(pages) + 1:03d}'
        dest = out / f'{page_id}.png'
        if dest in sources:
            raise ValueError('输出不得覆盖原文件。')
        image = rgb(image)
        image.save(dest, format='PNG')
        pages.append({'id': page_id, 'path': dest.name, 'source': source.name,
                      'source_page': source_page, 'width': image.width, 'height': image.height})

    for source in sources:
        if source.suffix.lower() == '.pdf':
            fitz = get_fitz()
            with fitz.open(source) as doc:
                if doc.needs_pass:
                    raise ValueError('PDF有密码，请提供已解密副本。')
                for idx, page in enumerate(doc):
                    if page.rect.width * page.rect.height * (dpi / 72) ** 2 > 30_000_000:
                        raise ValueError('PDF页面过大，请降低dpi或用已有工具分辨率受控地渲染。')
                    pix = page.get_pixmap(dpi=dpi, alpha=False, colorspace=fitz.csRGB)
                    emit(Image.open(io.BytesIO(pix.tobytes('png'))), source, idx + 1)
        else:
            with Image.open(source) as image:
                for idx in range(getattr(image, 'n_frames', 1)):
                    image.seek(idx)
                    emit(image.copy(), source, idx + 1)
    if not pages:
        raise ValueError('没有可处理的页面。')
    manifest = out / 'pages.json'
    save_json(manifest, {'pages': pages})
    return {'manifest': str(manifest), 'page_count': len(pages)}
