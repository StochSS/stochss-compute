# StochSS-Compute

StochSS-Compute is a compute delegation server for the [StochSS](https://github.com/StochSS) family of stochastic simulation software. StochSS-Compute allows for one to run StochSS or GillesPy2 simulations on distributed cloud compute resources.
***
<table><tr><td><b>
<img width="20%" align="right" src="https://raw.githubusercontent.com/StochSS/GillesPy2/develop/.graphics/stochss-logo.png">
<a href="https://docs.google.com/forms/d/12tAH4f8CJ-3F-lK44Q9uQHFio_mGoK0oY829q5lD7i4/viewform">PLEASE REGISTER AS A USER</a>, so that we can prove StochSS-Compute has many users when we seek funding to support development. StochSS-Compute is part of the <a href="http://www.stochss.org">StochSS</a> project.
</td></tr></table>

***
## Example Tutorial
#### 1. Run this Docker command:
```
docker run -it --rm -p 8888:8888 -p 8787:8787 stochss/stochss-compute:examples jupyter notebook
```
#### 2. Open the link provided by the Jupyter Notebook server in your browser.
#### 3. Open and run the self-contained `Tutorial-1.ipynb`
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
pip install requirements.txt
```
### OR
#### Global install of dependencies:
```
git clone https://github.com/StochSS/stochss-compute.git
cd stochss-compute
pip install requirements.txt
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
### 1. As an alternative to the above steps, you can use Docker.

```
docker run -it --rm --network host stochss/stochss-compute:latest
```

- Stochss-compute is now running on localhost:29681.
- The cache defaults to the current working directory under `cache`. To set a new path for the cache, you can pass one to `docker run`:
```
docker run -it --rm --network host -v $PWD/MyCache:/usr/src/app/cache stochss/stochss-compute
```

<!-- #### Minikube
- A third usage of StochSS compute it to use it with "Minikube", which is part of [Kubernetes](https://kubernetes.io/).
- Requires `minikube`, `docker`, and `kubectl` to be installed. Then:
```
minikube start
cd into kubernetes directory
kubectl apply -f api_deployment.yaml
minikube dashboard
```
- Now, wait for the stochss-compute container to be created.

- From here, there are two ways to access the cluster. -->

<!-- ##### To set up local access:
`minikube service --url stochss-compute-service`
- exposes external IP (on EKS or otherwise this is handled by your cloud provider)
- use this host and IP when calling ComputeServer()
- first time will be slow because the dask containers have to start up

##### To use ngrok to set up public access  (ngrok.com to sign up for a free account and download/install):
```
url=$(minikube service --url stochss-compute-service)
ngrok http $url
```
- use this URL when calling ComputeServer() -->


<!-- ## Usage

- The easiest way to run stochss-compute simulations is via Jupyter notebooks:

```python
import numpy, gillespy2

# Import stochss-compute.
from stochss-compute import RemoteSimulation, ComputeServer

# Define your GillesPy2 model.
class ToggleSwitch(gillespy2.Model):
    """ Gardner et al. Nature (1999)
    'Construction of a genetic toggle switch in Escherichia coli'
    """
    def __init__(self, parameter_values=None):
        gillespy2.Model.__init__(self, name="toggle_switch")
        
        # Parameters
        alpha1 = gillespy2.Parameter(name='alpha1', expression=1)
        alpha2 = gillespy2.Parameter(name='alpha2', expression=1)
        beta = gillespy2.Parameter(name='beta', expression="2.0")
        gamma = gillespy2.Parameter(name='gamma', expression="2.0")
        mu = gillespy2.Parameter(name='mu', expression=1.0)
        self.add_parameter([alpha1, alpha2, beta, gamma, mu])

        # Species
        U = gillespy2.Species(name='U', initial_value=10)
        V = gillespy2.Species(name='V', initial_value=10)
        self.add_species([U, V])

        # Reactions
        cu = gillespy2.Reaction(name="r1",reactants={}, products={U:1}, propensity_function="alpha1/(1+pow(V,beta))")
        cv = gillespy2.Reaction(name="r2",reactants={}, products={V:1}, propensity_function="alpha2/(1+pow(U,gamma))")
        du = gillespy2.Reaction(name="r3",reactants={U:1}, products={}, rate=mu)
        dv = gillespy2.Reaction(name="r4",reactants={V:1}, products={}, rate=mu)
        
        self.add_reaction([cu,cv,du,dv])
        self.timespan(numpy.linspace(0,100,101))
        
# Instantiate a new instance of the model.
model = ToggleSwitch()

# Run the model on a stochss-compute server instance running on localhost. 
# The default port is 1234, but will depend on how you choose to set it up.
results = RemoteSimulation.on(ComputeServer("127.0.0.1", port=1234)).with_model(model).run()

# Wait for the simulation to finish.
results.wait()

# Plot the results.
results.plot()
``` -->

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
