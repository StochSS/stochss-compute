'''
Cache for StochSS-Compute
'''
import os
from json.decoder import JSONDecodeError
from datetime import datetime
from filelock import SoftFileLock
from gillespy2 import Results

class Cache:
    '''
    Cache

    :param cache_dir: The root cache directory.
    :type cache_dir: str

    :param results_id: Simulation hash.
    :type results_id: str
    '''
    def __init__(self, cache_dir, results_id):
        self.results_path = os.path.join(cache_dir, f'{results_id}.results')
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)

    def create(self):
        '''
        Create the results file if it does not exist.

        :returns: None
        '''
        try:
            with open(self.results_path, 'x', encoding='utf-8') as file:
                file.close()
        except FileExistsError:
            pass

    def exists(self) -> bool:
        '''
        Check if the results file exists.
        '''
        return os.path.exists(self.results_path)

    def is_empty(self):
        '''
        Check if the results are empty.
        '''
        lock = SoftFileLock(f'{self.results_path}.lock')
        with lock:
            if self.exists():
                filesize = os.path.getsize(self.results_path)
                if filesize == 0:
                    return True
                return False
            else:
                return True

    def is_ready(self, n_traj_wanted) -> bool:
        '''
        Check if the results are ready to be retrieved from the cache.

        :param n_traj_wanted: The number of requested trajectories.
        :type int:
        '''
        results = self.get()
        if results is None or n_traj_wanted > len(results):
            return False
        return True

    def n_traj_needed(self, n_traj_wanted) -> int:
        '''
        Calculate the difference between the number of trajectories the user has requested
         and the number of trajectories currently in the cache.

        :param n_traj_wanted: The number of requested trajectories.
        :type int:
        '''
        if self.is_empty():
            return n_traj_wanted
        results = self.get()
        if results is None:
            return n_traj_wanted
        diff = n_traj_wanted - len(results)
        if diff > 0:
            return diff
        return 0

    def n_traj_in_cache(self) -> int:
        '''
        Check the number of trajectories in the cache.
        '''
        if self.is_empty():
            return 0
        results = self.get()
        if results is not None:
            return len(results)
        return 0

    def get(self) -> Results or None:
        '''
        Retrieve a gillespy2.Results object from the cache or None if error.
        '''
        try:
            results_json = self.read()
            return Results.from_json(results_json)
        except JSONDecodeError:
            return None

    def read(self) -> str:
        '''
        Retrieve a gillespy2.Results object as a JSON-formatted string.

        :returns:
        :type str:
        '''
        lock = SoftFileLock(f'{self.results_path}.lock')
        with lock:
            with open(self.results_path,'r', encoding='utf-8') as file:
                return file.read()

    def save(self, results: Results):
        '''
        Save a newly processed gillespy2.Results object to the cache.

        :param results: The new Results.
        :type gillespy2.Results:

        :returns:
        :type None:
        '''
        msg = f'{datetime.now()} | Cache | <{self.results_path}> | '
        lock = SoftFileLock(f'{self.results_path}.lock')
        with lock:
            with open(self.results_path, 'r+', encoding='utf-8') as file:
                try:
                    old_results = Results.from_json(file.read())
                    combined_results = results + old_results
                    print(msg+'Add')
                    file.seek(0)
                    file.write(combined_results.to_json())
                except JSONDecodeError:
                    print(msg+'New')
                    file.seek(0)
                    file.write(results.to_json())
