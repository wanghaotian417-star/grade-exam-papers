"""Validate evidence, scores and coordinates; calculate honest denominators."""
import json
from pathlib import Path
from collections import Counter
from .common import STATUSES, RUBRICS, DECIDED, number

def read_result(path):
    path = Path(path).resolve()
    def reject_constant(value):
        raise ValueError('JSON不允许NaN或Infinity：' + value)
    with path.open(encoding='utf-8') as file:
        data = json.load(file, parse_constant=reject_constant)
    errors = []
    def need(condition, message):
        if not condition:
            errors.append(message)
    if not isinstance(data, dict):
        raise ValueError('结果必须是JSON对象。')
    need(type(data.get('schema_version')) is int and data.get('schema_version') == 1,
         'schema_version必须为1。')
    need(isinstance(data.get('title'), str) and bool(data['title'].strip()), '缺少title。')
    need(data.get('rubric_source') in RUBRICS, 'rubric_source不合法。')
    notes = data.get('notes', [])
    need(isinstance(notes, list) and all(isinstance(x, str) for x in notes), 'notes须为字符串数组。')
    pages, questions = data.get('pages'), data.get('questions')
    if not isinstance(pages, list) or not pages:
        raise ValueError('pages必须为非空数组。')
    if not isinstance(questions, list) or not questions:
        raise ValueError('questions必须为非空数组。')
    page_ids, paths = set(), {}
    for idx, page in enumerate(pages):
        prefix = f'pages[{idx}]'
        if not isinstance(page, dict):
            errors.append(prefix + '须为对象。')
            continue
        page_id = page.get('id')
        if not isinstance(page_id, str) or not page_id:
            errors.append(prefix + '缺少字符串id。')
            continue
        need(page_id not in page_ids, prefix + '页ID重复。')
        page_ids.add(page_id)
        raw = page.get('path')
        if not isinstance(raw, str) or not raw or '://' in raw:
            errors.append(prefix + '需要本地path。')
            continue
        local = (path.parent / raw).resolve()
        need(local.is_file(), prefix + '图片不存在：' + str(local))
        paths[page_id] = local

    def region(value, prefix):
        if not isinstance(value, dict):
            errors.append(prefix + '须为对象。')
            return
        page_id = value.get('page')
        need(isinstance(page_id, str) and page_id in page_ids, prefix + '引用未知页。')
        box = value.get('bbox')
        valid = isinstance(box, list) and len(box) == 4 and all(number(v) for v in box)
        if valid:
            valid = 0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1
        need(valid, prefix + 'bbox须为0至1内、宽高为正的四坐标。')

    question_ids = set()
    for idx, q in enumerate(questions):
        prefix = f'questions[{idx}]'
        if not isinstance(q, dict):
            errors.append(prefix + '须为对象。')
            continue
        qid = q.get('id')
        if not isinstance(qid, str) or not qid:
            errors.append(prefix + '缺少字符串id。')
        else:
            need(qid not in question_ids, prefix + '题号重复。')
            question_ids.add(qid)
        status = q.get('status')
        need(isinstance(status, str) and status in STATUSES, prefix + 'status不合法。')
        for key in ('prompt', 'reference_answer', 'analysis'):
            need(isinstance(q.get(key), str), prefix + '.' + key + '须为字符串。')
        for key in ('topic', 'scoring_notes'):
            need(key not in q or isinstance(q[key], str), prefix + '.' + key + '须为字符串。')
        source = q.get('rubric_source', data.get('rubric_source'))
        need(isinstance(source, str) and source in RUBRICS, prefix + '评分来源不合法。')
        need('score' in q and 'max_score' in q, prefix + '须显式填写score和max_score，可为null。')
        score, maximum = q.get('score'), q.get('max_score')
        need(maximum is None or (number(maximum) and maximum > 0), prefix + '满分须为正数或null。')
        if score is not None:
            need(number(score) and number(maximum) and 0 <= score <= maximum,
                 prefix + '分数超界或缺少满分。')
            need(source in {'user', 'official', 'suggested'}, prefix + '给分必须声明评分来源。')
            if status == 'correct' and number(score) and number(maximum):
                need(score == maximum, prefix + 'correct须给满分；否则请修正状态或分数。')
            if status == 'partial' and number(score) and number(maximum):
                need(score < maximum, prefix + 'partial不可满分。')
            if status == 'unanswered':
                need(score == 0, prefix + '确认空白不可给正分。')
        if status in {'pending', 'not_provided'}:
            need(score is None, prefix + '待确认/未提供不可给分。')
        steps = q.get('student_steps')
        if not isinstance(steps, list):
            errors.append(prefix + '.student_steps须为数组。')
            steps = []
        if status in {'correct', 'partial', 'incorrect'}:
            need(bool(steps), prefix + '已判定作答必须保留学生步骤或答案。')
        for si, step in enumerate(steps):
            sp = f'{prefix}.student_steps[{si}]'
            if not isinstance(step, dict):
                errors.append(sp + '须为对象。')
                continue
            need(isinstance(step.get('text'), str), sp + '缺少text。')
            need(isinstance(step.get('page'), str) and step['page'] in page_ids, sp + '引用未知页。')
            if 'bbox' in step and step['bbox'] is not None:
                region(step, sp)
        need('first_error' in q, prefix + '须显式填写first_error，可为null。')
        first = q.get('first_error')
        if first is not None:
            if not isinstance(first, dict):
                errors.append(prefix + '.first_error须为对象或null。')
            else:
                si = first.get('step_index')
                need(type(si) is int and 0 <= si < len(steps), prefix + '首错索引越界。')
                for key in ('reason', 'correction'):
                    need(isinstance(first.get(key), str) and bool(first[key].strip()), prefix + '首错缺少' + key)
            need(status in {'partial', 'incorrect'}, prefix + '该状态不应标记已确认的首错。')
        if status == 'unanswered':
            need(not steps, prefix + '确认空白不应包含学生步骤。')
        regions = q.get('regions')
        if not isinstance(regions, list):
            errors.append(prefix + '.regions须为数组。')
            regions = []
        for ri, item in enumerate(regions):
            region(item, f'{prefix}.regions[{ri}]')
    if errors:
        raise ValueError('\n'.join(errors))
    return data, paths


def statistics(data):
    questions = data['questions']
    counts = Counter(q['status'] for q in questions)
    judged = sum(counts[s] for s in DECIDED)
    scored = [q for q in questions if q.get('score') is not None]
    earned = round(sum(q['score'] for q in scored), 8)
    possible = round(sum(q['max_score'] for q in scored), 8)
    complete = len(scored) == len(questions) and judged == len(questions)
    return {'provided_questions': len(questions), 'status_counts': {s: counts[s] for s in sorted(STATUSES)},
            'judged_questions': judged, 'accuracy_percent': round(100 * counts['correct'] / judged, 2) if judged else None,
            'scored_questions': len(scored), 'earned_scored': earned, 'possible_scored': possible,
            'complete_total': {'earned': earned, 'maximum': possible} if complete else None}
