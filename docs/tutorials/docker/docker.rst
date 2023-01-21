Tutorial Docker Container
=========================

1. Run:

.. code-block:: bash

    JUPYTER_PORT=7888 && \
    docker run -it --rm \
    -p $JUPYTER_PORT:$JUPYTER_PORT \
    -p 8787:8787 \ # for dask dashboard
    stochss/stochss-compute:tutorial \
    jupyter notebook \
    --port $JUPYTER_PORT

2. Open the link provided by the Jupyter Notebook server in your browser.

3. Open and run the self-contained `Tutorial_1-Local.ipynb`.

