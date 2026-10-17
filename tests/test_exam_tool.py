"""Integration checks with synthetic pages; no real exam data or model calls."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/grade-exam-papers/scripts'
sys.path.insert(0, str(SCRIPTS))
from exam_grader.common import save_json
from exam_grader.preparation import prepare
from exam_grader.validation import read_result, statistics
from exam_grader.reporting import export


class ExamToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pages = []
        for index in (1, 2):
            path = self.root / f'page{index}.png'
            Image.new('RGB', (600, 400), 'white').save(path)
            self.pages.append({'id': f'p{index:03d}', 'path': str(path)})

    def question(self, qid, status, score=None, maximum=None):
        steps = [{'page': 'p001', 'text': 'x=1'}] if status in {'correct', 'partial', 'incorrect'} else []
        return {'id': qid, 'status': status, 'prompt': '<script>not executable</script>',
                'student_steps': steps, 'reference_answer': 'Reference', 'analysis': 'Analysis',
                'first_error': None, 'score': score, 'max_score': maximum, 'regions': []}

    def data(self):
        return {'schema_version': 1, 'title': 'Test', 'rubric_source': 'user', 'pages': self.pages,
                'questions': [self.question('1', 'correct', 6, 6), self.question('2', 'partial', 2, 4),
                              self.question('3', 'pending', None, 5), self.question('4', 'not_provided'),
                              self.question('5', 'unanswered', 0, 2)]}

    def source(self, data):
        path = self.root / 'grading.json'
        save_json(path, data)
        return path

    def test_prepare_preserves_mapping_and_rejects_overwrite(self):
        out = self.root / 'prepared'
        result = prepare([self.pages[0]['path'], self.pages[1]['path']], out, 160)
        manifest = json.loads(Path(result['manifest']).read_text())
        self.assertEqual([p['id'] for p in manifest['pages']], ['p001', 'p002'])
        self.assertEqual(manifest['pages'][0]['source'], 'page1.png')
        with self.assertRaises(ValueError):
            prepare([self.pages[0]['path']], out, 160)

    def test_cross_page_steps_are_not_overwritten(self):
        data = self.data()
        steps = [{'page': 'p001', 'text': 'first'}, {'page': 'p002', 'text': 'second'}]
        data['questions'][0]['student_steps'] = steps
        loaded, _ = read_result(self.source(data))
        self.assertEqual(loaded['questions'][0]['student_steps'], steps)

    def test_pending_and_missing_excluded_from_denominator_and_score(self):
        stats = statistics(self.data())
        self.assertEqual(stats['judged_questions'], 3)
        self.assertEqual(stats['accuracy_percent'], 33.33)
        self.assertEqual((stats['earned_scored'], stats['possible_scored']), (8, 12))
        self.assertIsNone(stats['complete_total'])

    def test_no_judged_questions_has_no_accuracy(self):
        data = self.data()
        data['questions'] = [self.question('1', 'pending')]
        self.assertIsNone(statistics(data)['accuracy_percent'])

    def test_complete_total_requires_all_scores(self):
        data = self.data()
        data['questions'] = data['questions'][:2]
        self.assertEqual(statistics(data)['complete_total'], {'earned': 8, 'maximum': 10})

    def test_invalid_evidence_and_scores_are_rejected(self):
        cases = [
            lambda d: d['questions'][2].update(score=0),
            lambda d: d['questions'][0].update(score=True),
            lambda d: d['questions'][1].update(score=5),
            lambda d: d.update(rubric_source='none'),
            lambda d: d['questions'][0].update(id='2'),
            lambda d: d['questions'][0].update(student_steps=[]),
            lambda d: d['questions'][0]['student_steps'][0].update(page='missing'),
            lambda d: d['questions'][0].update(regions=[{'page': 'p001', 'bbox': [.9, .1, .2, .8]}]),
            lambda d: d['questions'][1].update(first_error={'step_index': 10, 'reason': 'r', 'correction': 'c'})]
        for mutation in cases:
            with self.subTest(mutation=cases.index(mutation)):
                data = self.data()
                mutation(data)
                with self.assertRaises(ValueError):
                    read_result(self.source(data))

    def test_html_escaping_coordinates_and_fresh_statistics(self):
        data = self.data()
        data['statistics'] = {'accuracy_percent': 100}
        data['questions'][0]['regions'] = [{'page': 'p001', 'bbox': [.1, .1, .7, .3]}]
        out = self.root / 'report'
        export(self.source(data), out)
        report = (out / 'report.html').read_text()
        self.assertNotIn('<script>', report)
        self.assertIn('&lt;script&gt;', report)
        self.assertIn('data:image/png;base64,', report)
        with Image.open(out / 'annotated-p001.png') as image:
            self.assertEqual(image.getpixel((round(.1 * 599), round(.2 * 399))), (20, 128, 74))
        result = json.loads((out / 'results.json').read_text())
        self.assertEqual(result['statistics']['accuracy_percent'], 33.33)

    def test_pdf_export_and_prepare_preserve_page_count(self):
        import fitz
        out = self.root / 'pdf-output'
        export(self.source(self.data()), out, True)
        with fitz.open(out / 'annotated-paper.pdf') as pdf:
            self.assertEqual(len(pdf), 2)
        result = prepare([out / 'annotated-paper.pdf'], self.root / 'pdf-pages', 100)
        self.assertEqual(result['page_count'], 2)

    def test_cli_works_from_other_working_directory(self):
        source = self.source(self.data())
        completed = subprocess.run([sys.executable, str(SCRIPTS / 'exam_tool.py'), 'validate', str(source)],
                                   cwd=self.root, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)['valid'])


if __name__ == '__main__':
    unittest.main()
