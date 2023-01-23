'''
test.run_unit_tests
'''
import os
import sys
import unittest
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('-m', '--mode', default='develop', choices=['develop', 'release'],
                    help='Run tests in develop mode or release mode.')

if __name__ == '__main__':
    args = parser.parse_args()
    if args.mode == 'develop':
        print('Running tests in develop mode. Appending repository directory to system path.')
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        sys.path.insert(1, '..')

    from test.unit_tests import test_hash, test_cache, test_launch, test_compute_server

    modules = [
        # test_hash,
        # test_cache,
        # test_launch,
        test_compute_server,
    ]
    for module in modules:
        suite = unittest.TestLoader().loadTestsFromModule(module)
        runner = unittest.TextTestRunner(failfast=args.mode == 'develop')

        print(f'Executing: {module}')
        result = runner.run(suite)
        print('=' * 70)
        if not result.wasSuccessful():
            sys.exit(not result.wasSuccessful())
    
