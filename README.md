# StochSS-Compute

With StochSS-Compute, you can run GillesPy2 simulations on your own server. Results are cached and anonymized, so you
can easily save and recall previous simulations. 

## Example Quick Start
First, clone the repository.
```
git clone https://github.com/StochSS/stochss-compute.git
cd stochss-compute
```
- If you are unfamiliar with python virtual environments, read this [documentation](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment) first.
- Note that you will have to activate your venv every time you run stochSS-compute, as well as for your dask scheduler and each of its workers.
- The following will set up the `dask-scheduler`, one `dask-worker`, the backend api server, and launch an example `jupyter` notebook.
- Each of these must be run in separate terminal windows in the main `stochss-compute` directory.
- Just copy and paste!
```
# Terminal 1
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
dask-scheduler
```
```
# Terminal 2
source venv/bin/activate
dask-worker localhost:8786
```
```
# Terminal 3
source venv/bin/activate
python3 app.py
```
- Stochss-compute is now running on localhost:1234.
<!-- - Dask compute cluster configuration parameters can be passed to `app.py`, see the [documentation](https://github.com/StochSS/stochss-compute/blob/dev/stochss_compute/api/delegate/dask_delegate.py#L20). -->

```
# Terminal 4
source venv/bin/activate
jupyter notebook --port=9999
```
- This notebook will show you how to use StochSS-compute.
- Jupyter should then launch automatically, where you can then navigate to the examples directory and open up StartHere.ipynb.
- If not, copy and paste the following URL into your web browser:  
`http://localhost:9999/notebooks/examples/StartHere.ipynb`
#### Docker

An alternative installation to the above method is to use docker. We host an image on docker hub you can download and use simply by running the following line.


```
docker run -p 1234:1234 mdip226/stochss-compute:latest
```

- The `-p` flag publishes the container's exposed port on the host computer, as in `-p <hostPort>:<containerPort>`
- Stochss-compute is now running on localhost:1234.

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
