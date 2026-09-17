# run.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

import pytest
import os

os.environ['TEST_ENV'] = os.getenv('TEST_ENV', 'dev')

def run_all_tests():
    args = [
        'testcases/',
        '-v',
        '--tb=short',
        '--html=reports/test_report.html',
        '--self-contained-html',
        '--alluredir=reports/allure-results',
        '-n','auto',
        '--dist', 'loadscope',
        '-maxfail=5'
    ]
    return pytest.main(args)

def run_smoke_tests():
    args = [
        'testcases/',
        '-m', 'smoke',
        '-v',
        '--html=reports/smoke_report.html',
        '--self-contained-html'
    ]
    return pytest.main(args)

def run_module(module_name: str):
    args = [
        f'testcases/admin/{module_name}',
        '-v',
        '--html=reports/module_report.html',
        '--self-contained-html'
    ]
    return pytest.main(args)

def run_with_allure():
    args = [
        'testcases/',
        '--alluredir=reports/allure-results',
        '-v',
        '-n', 'auto'
    ]
    return pytest.main(args)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'smoke':
            sys.exit(run_smoke_tests())
        elif sys.argv[1] == 'module' and len(sys.argv) > 2:
            sys.exit(run_module(sys.argv[2]))
        elif sys.argv[1] == 'allure':
            sys.exit(run_with_allure())
        else:
            print("Usage: python run.py [smoke|module <module_name>|allure]")
            sys.exit(0)
    else:
        sys.exit(run_all_tests())