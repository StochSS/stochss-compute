from datetime import datetime
import os
from gillespy2 import Results

from stochss_compute.core.errors import RemoteSimulationError

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
        
    def get(self) -> Results or None:
        if self.is_empty():
            return None
        try:
            results_json = self.read()
            return Results.from_json(results_json)

        except Exception:
            raise RemoteSimulationError('Malformed json')

    def read(self) -> str:
        with open(self.results_path,'r') as file:
            return file.read()

    def new(self, results: Results):
        with open(self.results_path, 'w') as file:
            file.write(results.to_json())

    def add(self, new_results: Results):
        old_results = self.get()
        combined_results = new_results + old_results
        with open(self.results_path,'w') as file:
            file.write(combined_results.to_json())

    def save(self, results: Results):
        msg = f'{datetime.now()} | Cache | <{self.results_path}> | '
        if self.is_empty():
            print(msg+'New')
            self.new(results)
        else:
            print(msg+'Add')
            self.add(results)