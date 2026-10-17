"""Export escaped offline reports and deterministic page annotations."""
import base64
import html
from pathlib import Path
from .common import get_pillow, get_fitz, rgb, save_json, COLORS, TAGS, LABELS
from .validation import read_result, statistics

def export(path, out, pdf=False):
    data, paths = read_result(path)
    Image, ImageDraw, _ = get_pillow()
    fitz = get_fitz() if pdf else None
    out = Path(out).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError('输出目录非空；请选择新的报告目录。')
    out.mkdir(parents=True, exist_ok=True)
    # Numeric output names prevent page/question IDs from becoming filesystem paths.
    marked = []
    figures = []
    for idx, page in enumerate(data['pages'], 1):
        with Image.open(paths[page['id']]) as original:
            image = rgb(original)
        draw = ImageDraw.Draw(image)
        line_width = max(2, round(min(image.size) / 350))
        from PIL import ImageFont
        font_size = max(14, round(min(image.size) / 60))
        try:
            font = ImageFont.truetype('DejaVuSans.ttf', font_size)
        except OSError:
            try:
                font = ImageFont.load_default(size=font_size)
            except TypeError:
                font = ImageFont.load_default()
        for qi, q in enumerate(data['questions'], 1):
            for region in q['regions']:
                if region['page'] != page['id']:
                    continue
                b = region['bbox']
                box = (round(b[0] * (image.width - 1)), round(b[1] * (image.height - 1)),
                       round(b[2] * (image.width - 1)), round(b[3] * (image.height - 1)))
                color = COLORS[q['status']]
                draw.rectangle(box, outline=color, width=line_width)
                label = f'{TAGS[q["status"]]} #{qi}'
                tb = draw.textbbox((0, 0), label, font=font)
                tw, th = tb[2] - tb[0] + 8, tb[3] - tb[1] + 8
                tx = max(0, min(box[0], image.width - tw))
                ty = max(0, box[1] - th)
                draw.rectangle((tx, ty, min(image.width - 1, tx + tw), min(image.height - 1, ty + th)), fill='white', outline=color)
                draw.text((tx + 4, ty + 4 - tb[1]), label, fill=color, font=font)
        dest = out / f'annotated-p{idx:03d}.png'
        image.save(dest)
        marked.append(dest)
        encoded = base64.b64encode(dest.read_bytes()).decode('ascii')
        figures.append(f'<figure><figcaption>{html.escape(page["id"])}</figcaption><img alt="标注试卷" src="data:image/png;base64,{encoded}"></figure>')
    stats = statistics(data)
    esc = lambda value: html.escape(str(value))
    pre = lambda value: '<div class="text">' + esc(value) + '</div>'
    rows, details = [], []
    for idx, q in enumerate(data['questions'], 1):
        mark = '未评分' if q['score'] is None else f'{q["score"]} / {q["max_score"]}'
        source = q.get('rubric_source', data['rubric_source'])
        rows.append(f'<tr><td>{idx}</td><td>{esc(q["id"])}</td><td>{LABELS[q["status"]]}</td><td>{mark}</td><td>{esc(source)}</td></tr>')
        steps = ''.join('<li>' + pre(s['text']) + '<small>页 ' + esc(s['page']) + '</small></li>' for s in q['student_steps'])
        first = q['first_error']
        error = ''
        if first:
            step = q['student_steps'][first['step_index']]['text']
            error = '<h4>第一处实质错误</h4>' + pre(step) + pre('原因：' + first['reason']) + pre('修正：' + first['correction'])
        location = '' if q['regions'] else '<p class="muted">未提供可靠标注坐标，本题未在原图定位。</p>'
        details.append(f'<article><h3>标注#{idx} · 第{esc(q["id"])}题 · {LABELS[q["status"]]}</h3>'
                       + '<h4>题干</h4>' + pre(q['prompt']) + '<h4>学生完整步骤</h4><ol>' + steps + '</ol>'
                       + error + '<h4>分析</h4>' + pre(q['analysis']) + '<h4>参考解答</h4>' + pre(q['reference_answer'])
                       + pre('知识点：' + q.get('topic', '')) + pre('评分说明：' + q.get('scoring_notes', '')) + location + '</article>')
    accuracy = '无可判定题目' if stats['accuracy_percent'] is None else str(stats['accuracy_percent']) + '%'
    summary = f'已提供 {len(data["questions"])} 题；已明确判断 {stats["judged_questions"]} 题；整题正确率 {accuracy}。'
    if stats['scored_questions']:
        summary += f'已评分 {stats["scored_questions"]} 题：{stats["earned_scored"]} / {stats["possible_scored"]} 分（仅已评分题）。'
    else:
        summary += '本次未给分，仅提供判题与分析。'
    if stats['complete_total'] is None:
        summary += '存在未评分或未确定内容，不报告整卷总分。'
    else:
        summary += '已提供范围内全部题目均已评分。'
    notes = ''.join('<li>' + esc(n) + '</li>' for n in data.get('notes', []))
    css = ('body{font:16px/1.65 system-ui,sans-serif;max-width:1100px;margin:32px auto;padding:0 22px;color:#18212b;background:#f8fafc}'
           'h1,h2,h3{line-height:1.3}article,figure{background:white;padding:22px;margin:24px 0;border:1px solid #dde3ea;border-radius:10px}'
           'table{border-collapse:collapse;width:100%;background:white}td,th{padding:10px;border:1px solid #cbd5e1;text-align:left}'
           'img{max-width:100%;height:auto}.text{white-space:pre-wrap;overflow-wrap:anywhere}.muted,small{color:#526174}'
           '@media print{body{margin:0;background:white}article{break-inside:avoid}figure{break-before:page;border:0;padding:0}}')
    document = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                + '<title>' + esc(data['title']) + '</title><style>' + css + '</style><body><h1>' + esc(data['title']) + '</h1>'
                + pre(summary) + '<p class="muted">评分来源：user=用户细则；official=已提供的正式细则；suggested=建议细则；none=未评分。'
                + '红=错误，橙=部分正确，绿=正确，蓝=待确认/缺资料。公式以文本/LaTeX源码显示。</p><ul>' + notes + '</ul>'
                + '<table><thead><tr><th>标注</th><th>题号</th><th>结论</th><th>得分/满分</th><th>评分来源</th></tr></thead><tbody>'
                + ''.join(rows) + '</tbody></table><h2>逐题批改</h2>' + ''.join(details) + '<h2>原卷标注</h2>' + ''.join(figures) + '</body></html>')
    report = out / 'report.html'
    report.write_text(document, encoding='utf-8')
    files = {'report': str(report), 'annotated_images': [str(p) for p in marked]}
    if pdf:
        target = out / 'annotated-paper.pdf'
        with fitz.open() as doc:
            for source in marked:
                with Image.open(source) as image:
                    width, height = image.size
                page = doc.new_page(width=width * 72 / 160, height=height * 72 / 160)
                page.insert_image(page.rect, filename=str(source))
            doc.save(target)
        files['annotated_pdf'] = str(target)
    result_path = out / 'results.json'
    files['results'] = str(result_path)
    save_json(result_path, {**data, 'statistics': stats, 'output_files': files})
    return {'statistics': stats, 'files': files}
