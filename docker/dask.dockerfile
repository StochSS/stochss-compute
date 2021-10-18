FROM daskdev/dask

RUN dask-scheduler --host localhost

RUN dask-worker localhost:8786

EXPOSE 8786

