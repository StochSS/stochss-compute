'''
test.unit_tests.test_launch
'''
import os
import subprocess
import time
import unittest
from gillespy2 import Model
from stochss_compute.launch import launch_server, launch_with_cluster


class LaunchTest(unittest.TestCase):
    '''
    Test cache functioniality.
    '''
    cache_dir = 'cache'
    def setUp(self) -> None:
        if os.path.exists(self.cache_dir):
            with subprocess.Popen(['rm', '-r', self.cache_dir]) as r_m:
                r_m.wait()
        if not os.path.exists(self.cache_dir):
            with subprocess.Popen(['mkdir', self.cache_dir]) as mkdir:
                mkdir.wait()

    def tearDown(self) -> None:
        if os.path.exists(self.cache_dir):
            with subprocess.Popen(['rm', '-r', self.cache_dir]) as r_m:
                r_m.wait()

    # note: coverage does not pick this up TODO
    def test_launch_server(self):
        '''
        Calls the function.
        '''
        _LOCAL = False
        env = {}
        env['PATH'] = '../env/bin'
        if _LOCAL:
            env['PYTHONPATH'] = '../env/lib/python3.11/site-packages'
        with subprocess.Popen(['python', '-m', 'stochss_compute.launch'], env=env) as server:
            time.sleep(5)
            server.terminate()
            server.kill()
            server.wait()

    # note: coverage does not pick this up TODO
    def test_launch_with_cluster(self):
        '''
        Calls the function.
        '''
        _LOCAL = False
        env = {}
        env['PATH'] = '../env/bin'
        if _LOCAL:
            env['PYTHONPATH'] = '../env/lib/python3.11/site-packages'
        with subprocess.Popen(['python', '-m', 'stochss_compute.launch', 'cluster'], env=env) as server:
            time.sleep(5)
            server.terminate()
            server.kill()
            server.wait()
