Client
######

The core functionality of StochSS-Compute comes from GillesPy2.
This documentation assumes basic familiarity with 
`GillesPy2 <https://stochss.github.io/GillesPy2/docs/build/html/index.html>`_ 
and/or `StochSS <https://stochss.org/documentation/>`_.


1. To run a `RemoteSimulation </classes/stochss_compute.core.html#stochss_compute.core.remote_simulation.RemoteSimulation>`_, 
   you need a 
   `Model <https://stochss.github.io/GillesPy2/docs/build/html/classes/gillespy2.core.html#gillespy2.core.model.Model>`_ 
   and optionally a 
   `Solver <https://stochss.github.io/GillesPy2/docs/build/html/classes/gillespy2.core.html#gillespy2.core.gillespySolver.GillesPySolver>`_ 
   and `Server </classes/stochss_compute.client.html#stochss_compute.client.server.Server>`_. 
   More information about models may be found 
   `here <https://stochss.github.io/GillesPy2/docs/build/html/getting_started/basic_usage/basic_usage.html#simple-example-of-using-gillespy2>`_.

.. code-block:: python

    from gillespy2 import Model
    from gillespy2 import TauHybridSolver, TauHybridCSolver, NumPySSASolver, SSACSolver, CLESolver, TauLeapingSolver, TauLeapingCSolver, ODESolver, ODECSolver
    from stochss_compute import RemoteSimulation, ComputeServer
 
.. code-block:: python

    simulation = RemoteSimulation(model=model, host='localhost', solver=TauHybridSolver)


2. That's it. 

.. code-block:: python

    results = simulation.run()
    # returns right away

    results.plot()
    # polls the server, downloading results when complete

If a cached 
`Results <https://stochss.github.io/GillesPy2/docs/build/html/classes/gillespy2.core.html#gillespy2.core.Results>`_ 
object has identical properties to the simulation you have requested, your results are processed instantly. 

.. code-block:: python

    results2 = simulation.run()
    # returns cached object
    
    results2.plot()
    # no need to fetch

Server
######

1. Run the included command-line utility to launch a server and pre-configured `Dask <https://www.dask.org/>`_ cluster.

.. code-block:: bash

    stochss-compute-cluster

Arguments
*********

``-p PORT --port PORT``
    The port to use for the server. Defaults to 29681.

``-c CACHE, --cache CACHE``
    Path to use for the cache. Defaults to ``./cache``.
``--rm``
    Whether to delete the cache upon exit. Default False.

``-H DASK_HOST, --dask-host DASK_HOST``
    The host to use for the dask scheduler. Defaults to localhost.
``-P DASK_SCHEDULER_PORT, --dask-scheduler-port DASK_SCHEDULER_PORT``
    The port to use for the dask scheduler. 0 for a random port. Defaults to a random port.
``-W DASK_N_WORKERS, --dask-n-workers DASK_N_WORKERS``
    Configure the number of workers. Defaults to one per core.
``-T DASK_THREADS_PER_WORKER, --dask-threads-per-worker DASK_THREADS_PER_WORKER``
    Configure the threads per worker. Default will let Dask decide based on your CPU.
``--dask-processes DASK_PROCESSES``
    Whether to use processes (True) or threads (False). Defaults to True, unless worker_class=Worker, in which case it defaults to False.
``-D DASK_DASHBOARD_ADDRESS, --dask-dashboard-address DASK_DASHBOARD_ADDRESS``
    Address on which to listen for the Bokeh diagnostics server like ‘localhost:8787’ or ‘0.0.0.0:8787’.
    Defaults to ‘:8787’. Set to None to disable the dashboard. Use ‘:0’ for a random port.
``-N DASK_NAME, --dask-name DASK_NAME``
    A name to use when printing out the cluster, defaults to type name.


Connecting to a Dask Cluster
****************************

.. code-block:: bash

    stochss-compute -H localhost -P 8786

