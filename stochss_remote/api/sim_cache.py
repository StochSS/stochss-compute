import pathlib

from pip._internal import main as pip
from distutils.dir_util import copy_tree

class SimCache():
    def install(target, name, version):
        cache_path = pathlib.Path(f"cache/sims/{name}-{version}/")

        # This isn't the best way to script with pip, but it works for now. Will fix later.
        if not pathlib.Path(cache_path).exists():
            pip(["install", f"--target={cache_path}", f"{name}=={version}"])

        # Install the sim into the job directory.
        copy_tree(str(cache_path), str(target))
    