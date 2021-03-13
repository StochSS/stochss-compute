import pathlib
import shutil
from pip._internal import main as pip

class DepCache():
    def install(target, name, version):
        # If we already have a cached version of the dep on disk, copy it over instead.
        cache_path = pathlib.Path(f"cache/deps/{name}/{version}/")
        if (not pathlib.Path(cache_path.exists()):
            pip(["install", f"--target={cache_path}", f"{name}=={version}"])

        shutil.copy(target, cache_path)
    