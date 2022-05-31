# StochSS-Compute

With StochSS-Compute, you can run GillesPy2 simulations on your own server. Results are cached and anonymized, so you
can easily save and recall previous simulations. 

## Example Quick Start

### 1. Installing dependencies & `stochss_compute`
#### Using a python virtual environment ([documentation](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment)):
```
git clone https://github.com/StochSS/stochss-compute.git
cd stochss-compute
python3 -m venv venv 
source venv/bin/activate
pip3 install -r requirements.txt
```
### OR
#### Global install of dependencies:
```
git clone https://github.com/StochSS/stochss-compute.git
cd stochss-compute
pip3 install -r requirements.txt
```
### PyPI:
```
pip3 install stochss_compute
```

### 2. Start up the server and compute backend
#### Using the startup script dialogue:
```
python3 startup.py
```
<!-- #### Configure your compute setup by editing the file `daskconfig.ini` or passing arguments to `startup.py`:
```
python3 startup.py --daskconfig daskconfig.ini
``` -->
### 3. An example is contained in `./examples/StartHere.ipynb`:
```
# source venv/bin/activate # Uncomment if using a virtual environment
jupyter notebook --port 9999 examples/StartHere.ipynb
```
- Jupyter should launch automatically. If not, copy and paste the following URL into your web browser:  
`http://localhost:9999/notebooks/examples/StartHere.ipynb`

## Docker

```
docker run -it --rm --network host -p 29681:29681 stochss/stochss-compute:latest
```

- Stochss-compute is now running on localhost:29681.
- The cache defaults to the current working directory under `sd-cache`. To set a new path for the cache, you can pass one to `docker run`:
```
docker run -it --rm --network host -v $PWD/MyCache:/usr/src/app/sd-cache stochss/stochss-compute
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
