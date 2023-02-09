# StochSS-Compute

StochSS-Compute is a compute delegation server for the [StochSS](https://github.com/StochSS) family of stochastic simulation software. StochSS-Compute allows for one to run StochSS or GillesPy2 simulations on distributed cloud compute resources.
***
<table><tr><td><b>
<img width="20%" align="right" src="https://raw.githubusercontent.com/StochSS/GillesPy2/develop/.graphics/stochss-logo.png">
<a href="https://docs.google.com/forms/d/12tAH4f8CJ-3F-lK44Q9uQHFio_mGoK0oY829q5lD7i4/viewform">PLEASE REGISTER AS A USER</a>, so that we can prove StochSS-Compute has many users when we seek funding to support development. StochSS-Compute is part of the <a href="http://www.stochss.org">StochSS</a> project.
</td></tr></table>

***
## Installation 

#### 1. Installing dependencies & `stochss_compute`
#### PyPI Install:
```
pip install stochss_compute
```
#### Start up the server along with dask cluster:
```
stochss-compute-cluster
```
#### If you already have a dask cluster running on localhost:8786:
```
stochss-compute
```
***
### Git Clone Install
#### Using a python virtual environment ([documentation](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment)):
```
git clone https://github.com/StochSS/stochss-compute.git
cd stochss-compute
python -m venv venv 
source venv/bin/activate
pip install -r requirements.txt
```
### OR
#### Global install of dependencies:
```
git clone https://github.com/StochSS/stochss-compute.git
cd stochss-compute
pip install -r requirements.txt
```

### 2. Start up the server and compute backend
#### Using the startup script, which starts up a dask cluster, along with scheduler and workers:
```
python -m stochss_compute.launch cluster 
```
#### If you already have a dask cluster running on localhost:8786:
```
python -m stochss_compute.launch
```

## Docker
### As an alternative to the above steps, you can use Docker.
***
## Example Tutorial
#### 1. Run this Docker command:
```
JUPYTER_PORT=7888 && \
docker run -it --rm \
-p $JUPYTER_PORT:$JUPYTER_PORT \
-p 8787:8787 \ # for dask dashboard
stochss/stochss-compute:examples \
jupyter notebook \
--port $JUPYTER_PORT
```
#### 2. Open the link provided by the Jupyter Notebook server in your browser.
#### 3. Open and run the self-contained `Tutorial_1-Local.ipynb`
***
## Starting a server

```
docker run -it --rm --network host stochss/stochss-compute:latest
```

- Stochss-Compute is now running on localhost:29681.
- The cache defaults to the current working directory under `cache`. To set a new path for the cache, you can pass one to `docker run`:
```
docker run -it --rm --network host -v $PWD/MyCache:/usr/src/app/cache stochss/stochss-compute
```
***
## Cache Behavior
- Simulation results are given a unique identifier based upon the type of solver/algorithm, the model itself, and any other arguments passed to that simulation's `run()` call.
- Results are stored on disk in json format. 
- Results are 'anonymized', that is, variables and parameter names are converted to unique alphanumeric identifiers.
- Subsequent requests that match to cached results will automatically return the cached results.
- All other factors being the same, requests that differ only in the `number_of_trajectories` are associated with the same results object.
***

License
-------

StochSS-Compute is licensed under the GNU General Public License version 3.  Please see the file [LICENSE](https://github.com/StochSS/stochss-compute/blob/main/LICENSE.md) for more information.

Acknowledgments
---------------

This work has been funded by National Institutes of Health (NIH) NIBIB Award No. 2R01EB014877-04A1.

StochSS-Compute uses numerous open-source packages, without which it would have been effectively impossible to develop this software with the resources we had.  We want to acknowledge this debt.  In alphabetical order, the packages are:

* [Jupyter](https://jupyter.org) &ndash; web application for creating documents containing code, visualizations and narrative text
* [Dask.Distributed](https://distributed.dask.org) &ndash; a library for distributed computation

Finally, we are grateful for institutional resources made available by the [University of North Carolina at Asheville](https://www.unca.edu), the [University of California at Santa Barbara](https://ucsb.edu), and [Uppsala University](https://www.it.uu.se).

<div align="center">
  <a href="https://www.nigms.nih.gov">
    <img width="100" height="100" src="https://raw.githubusercontent.com/StochSS/GillesPy2/develop/.graphics/US-NIH-NIGMS-Logo.png">
  </a>
  &nbsp;&nbsp;
  <a href="https://www.unca.edu">
    <img height="102" src="https://raw.githubusercontent.com/StochSS/GillesPy2/develop/.graphics/UNCASEAL_blue.png">
  </a>
  &nbsp;&nbsp;
  <a href="https://www.ucsb.edu">
    <img height="108" src="https://raw.githubusercontent.com/StochSS/GillesPy2/develop/.graphics/ucsb-seal-navy.jpg">
  </a>
  &nbsp;&nbsp;
  <a href="https://www.it.uu.se">
    <img height="115" src="https://raw.githubusercontent.com/StochSS/GillesPy2/develop/.graphics/uppsala-universitet-logo-svg-vector.png">
  </a>
</div>
