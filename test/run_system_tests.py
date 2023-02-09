'''
test.run_system_tests
'''
import os
import sys
import unittest
import argparse
import importlib

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--mode', default='develop', choices=['develop', 'release'],
                    help='Run tests in develop mode or release mode.')
parser.add_argument('-c', '--case',required=False, type=str)

if __name__ == '__main__':
    args = parser.parse_args()
    if args.mode == 'develop':
        print('Running tests in develop mode. Appending repository directory to system path.')
        sys.path.insert(1, '..')

    if args.case is not None:
        modules = [importlib.import_module(f'system_tests.test_{args.case}')]
    else:
        modules = []
        import system_tests
        for name, module in sys.modules.items():
            if name.startswith('system_tests.test_'):
                modules.append(module)

    for module in modules:

        print(f'Executing: {module}')
        suite = unittest.TestLoader().loadTestsFromModule(module)
        runner = unittest.TextTestRunner(failfast=args.mode == 'develop')

        result = runner.run(suite)
        print('=' * 70)
        if not result.wasSuccessful():
            sys.exit(not result.wasSuccessful())
    
