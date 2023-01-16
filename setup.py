'''
StochSS-Compute
'''
# Note: how to do a PyPI release
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Run the following commands:
#
#   python3 setup.py sdist bdist_wheel
#   twine upload dist/*
#
# =============================================================================

from os import path
from setuptools import setup, find_packages


# The following reads the variables without doing an "import handprint",
# because the latter will cause the python execution environment to fail if
# any dependencies are not already installed -- negating most of the reason
# we're using setup() in the first place.  This code avoids eval, for security.

SETUP_DIR = path.dirname(path.abspath(__file__))

with open(path.join(SETUP_DIR, 'requirements.txt'), encoding='utf-8') as f:
    reqs = f.read().rstrip().splitlines()

with open(path.join(SETUP_DIR, "README.md"), "r", errors="ignore", encoding='utf-8') as f:
    readme = f.read()

version = {}
with open(path.join(SETUP_DIR, "stochss_compute/__version__.py"), encoding='utf-8') as f:
    text = f.read().rstrip().splitlines()
    variables = [line for line in text if line.startswith("__") and "=" in line]
    for v in variables:
        setting = v.split("=")
        version[setting[0].strip()] = setting[1].strip().replace("\"", "")

setup(name=             version["__title__"],
      version=          version["__version__"],
      description=      version["__description__"],
      author=           version["__author__"],
      author_email=     version["__email__"],
      url=              version["__url__"],
      license=          version["__license__"],
      packages=         find_packages("."),
      entry_points={
            'console_scripts': [
                'stochss-compute=stochss_compute.launch',
                'stochss-compute-cluster=stochss_compute.launch:launch_with_cluster',
            ]
        },
      install_requires= reqs,
      extras_requires = {
          'aws': [
              'boto3 == 1.24.71',
              'paramiko == 2.11.0',
              'python-dotenv == 0.21.0'
          ],
      },
      long_description= readme,
      long_description_content_type= "text/markdown",
      classifiers=      [
          "Development Status :: 5 - Production/Stable",
          "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
          "Operating System :: OS Independent",
          "Programming Language :: Python :: 3",
          "Topic :: Scientific/Engineering",
          "Topic :: Scientific/Engineering :: Chemistry",
          "Topic :: Scientific/Engineering :: Mathematics",
          "Topic :: Scientific/Engineering :: Medical Science Apps.",
          "Intended Audience :: Science/Research"
      ],

)
