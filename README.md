## Installation

#### Docker

The easiest way to get stochss-compute running is with docker. Clone the repository and run the following in the root directory:

```
docker-compose up --build
```
#### `minikube`
- first requires `minikube`, `docker`, and `kubectl` to be installed. Then:
```
minikube start
cd into kubernetes directory
kubectl apply -f api_deployment.yaml`
minikube dashboard
```
- Now, wait for the stochss-compute container to be created.

From here, there are two ways to access the cluster.

Option 1: To set up local access
`minikube service --url stochss-compute-service`
- to expose external IP (on EKS or otherwise this is handled by your cloud provider)
- use this host and IP when calling ComputeServer()
- first time will be slow because the dask containers have to start up

Option 2: To use ngrok to set up public access  (ngrok.com to sign up for a free account and download/install)
- `url=$(minikube service --url stochss-compute-service)`
- `ngrok http $url`
- use this URL when calling ComputeServer()

#### Manually

Ensure that the following dependencies are installed with your package manager of choice:

- `python-poetry`
- `redis`

Clone the repository and navigate into the new `stochss-compute` directory. Once inside, execute the following command to install the Python dependencies:

```
poetry install
```

And to activate the new virtual environment:

```
poetry shell
```

Once complete, both `celery` and `redis` need to be running.

```
celery -A stochss_compute.api worker -l INFO
```

`redis` can be run in several ways. If you prefer a `systemd` daemon:

```
sudo systemctl start redis
```

Otherwise:

```
redis-server
```

Finally, start the stochss-compute server.

```
poetry run stochss-compute
```

## Usage

Simulations are run on stochss-compute via Jupyter notebooks.

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
results = RemoteSimulation.on(ComputeServer("127.0.0.1", port=1234).with_model(model).run()

# Plot the results.
results.plot()
```
