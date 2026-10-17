#!/usr/bin/env python3
"""CLI for local page preparation and evidence-linked grading export; no model calls."""
import argparse
import json
from exam_grader.preparation import prepare
from exam_grader.validation import read_result, statistics
from exam_grader.reporting import export

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    prep = subs.add_parser('prepare', help='Prepare full pages, without OCR or grading')
    prep.add_argument('inputs', nargs='+')
    prep.add_argument('--out', required=True)
    prep.add_argument('--dpi', type=int, default=160)
    val = subs.add_parser('validate', help='Validate result data and local references')
    val.add_argument('result')
    exp = subs.add_parser('export', help='Export AI-authored grading data')
    exp.add_argument('result')
    exp.add_argument('--out', required=True)
    exp.add_argument('--pdf', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            output = prepare(args.inputs, args.out, args.dpi)
        elif args.command == 'validate':
            data, _ = read_result(args.result)
            output = {'valid': True, 'statistics': statistics(data)}
        else:
            output = export(args.result, args.out, args.pdf)
        print(json.dumps(output, ensure_ascii=False, allow_nan=False))
    except (ValueError, OSError, TypeError, KeyError) as exc:
        parser.exit(2, f'错误：{exc}\n')


if __name__ == '__main__':
    main()
