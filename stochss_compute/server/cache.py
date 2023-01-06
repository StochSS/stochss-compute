import os
from datetime import datetime
from filelock import Timeout, SoftFileLock
from gillespy2 import Results
from json.decoder import JSONDecodeError
from stochss_compute.core.errors import CacheError

class Cache:

    def __init__(self, cache_dir, results_id) -> None:
        self.results_path = os.path.join(cache_dir, f'{results_id}.results')
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)

    def create(self):
        if not self.exists():
            return open(self.results_path, 'x').close()
        else:
            raise CacheError('cache.create() called but file exists.')

    def exists(self) -> bool:
        return os.path.exists(self.results_path)

    def is_empty(self):
        if self.exists():
            filesize = os.path.getsize(self.results_path)
            if filesize == 0:
                return True
            else:
                return False
        else:
            return True

    def is_ready(self, n_traj_wanted) -> bool:
        results = self.get()
        if results is None or n_traj_wanted > len(results):
            return False
        return True

    def n_traj_needed(self, n_traj_wanted) -> int:
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
        if self.is_empty():
            return 0
        results = self.get()
        if results is not None:
            return len(results)
        return 0
  
    def get(self) -> Results or None:
        try:
            results_json = self.read()
            return Results.from_json(results_json)
        except JSONDecodeError:
            return None

    def read(self) -> str:
        with open(self.results_path,'r') as file:
            return file.read()

    # def add(self, new_results: Results):
    #     with open(self.results_path,'w') as file:
    #         file.write(new_results.to_json())

    def save(self, results: Results):
        msg = f'{datetime.now()} | Cache | <{self.results_path}> | '
        if self.exists():
            lock = SoftFileLock(f'{self.results_path}.lock')
            with lock:
                with open(self.results_path, 'r+') as file:
                    results_json = file.read()
                    try:
                        old_results = Results.from_json(results_json)
                        combined_results = results + old_results
                        print(msg+'Add')
                        file.seek(0)
                        file.write(combined_results.to_json())
                    except JSONDecodeError:
                        file.seek(0)
                        print(msg+'New')
                        file.write(results.to_json())
        else:
            raise CacheError('cache.save() called but results path has not been created yet.')
