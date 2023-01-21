Installation
############

StochSS-Compute can be installed on your computer using different methods.


Preferred method: using PyPI
****************************

Using Python 3 on **Linux**, **macOS**, and **Windows** operating systems, you should be able to install StochSS-Compute using the package management system `pip <https://pip.pypa.io/en/stable/installation/>`_ by typing the following commands in a command shell interpreter::

    python3 -m pip install stochss_compute --user --upgrade


Alternative methods: using the code repository
**********************************************

As an alternative to getting it from PyPI, you can instruct ``pip`` to install StochSS-Compute directly from the `GitHub repository for GillesPy2 <https://github.com/stochss/stochss-compute>`_ by using the following command::

    python3 -m pip install git+https@github.com:stochss/stochss-compute.git --user --upgrade


As a final alternative, you can first use ``git`` to clone a copy of the StochSS-Compute source tree from the GitHub repository and then install it using that copy::

    git clone --recursive https@github.com:stochss/stochss-compute.git
    cd stochss-compute
    python3 -m pip install . --user --upgrade
