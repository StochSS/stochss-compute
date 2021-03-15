import pathlib
import shutil
from pip._internal import main as pip
from distutils.dir_util import copy_tree

class DepCache():
    def install(target, name, version):
        cache_path = pathlib.Path(f"cache/sims/{name}-{version}/")

        # If we don't have the sim cached, install it via pip into the sim directory.
        if (not pathlib.Path(cache_path).exists()):
            pip(["install", f"--target={cache_path}", f"{name}=={version}"])

        # Install the sim into the job directory.
        copy_tree(str(cache_path), str(target))
    