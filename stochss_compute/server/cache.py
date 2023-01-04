import os
from datetime import datetime

from gillespy2 import Results
from json.decoder import JSONDecodeError
from stochss_compute.core.errors import CacheError, RemoteSimulationError

class Cache:
    def __init__(self, cache_dir, results_id) -> None:
        self.results_path = os.path.join(cache_dir, f'{results_id}.results')
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)

    def create(self):
        if not self.exists():
            return open(self.results_path, 'x').close()

    def exists(self) -> bool:
        return os.path.exists(self.results_path)

    def is_empty(self):
        if self.exists():
            with open(self.results_path, 'r') as file:
                if file.read(1) == '':
                    file.seek(0)
                    return True
                else:
                    file.seek(0)
                    return False
        else:
            return True

    def is_ready(self, n_traj) -> bool:
        results = self.get()
        if n_traj > len(results):
            return False
        return True

    def n_traj_needed(self, n_traj) -> int:
        if self.is_empty():
            return n_traj
        results = self.get()
        diff = n_traj - len(results)
        if diff > 0:
            return diff
        return 0

    def n_traj_in_cache(self) -> int:
        if self.is_empty():
            return 0
        results = self.get()
        return len(results)

        
    def get(self) -> Results or None:
        try:
            results_json = self.read()
            return Results.from_json(results_json)
        except JSONDecodeError:
            return None

    def read(self) -> str:
        with open(self.results_path,'r') as file:
            return file.read()

    def add(self, new_results: Results):
        with open(self.results_path,'w') as file:
            file.write(new_results.to_json())

    def save(self, results: Results):
        msg = f'{datetime.now()} | Cache | <{self.results_path}> | '
        old_results = self.get()
        if old_results is None:
            print(msg+'New')
            self.add(results)
        else:
            combined_results = results + old_results
            print(msg+'Add')
            self.add(combined_results)