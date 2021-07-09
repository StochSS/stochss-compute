import click

from redis import Redis
from distributed.diagnostics.plugin import SchedulerPlugin

from stochss_compute import RemoteSimulation

class DaskWorkerPlugin(SchedulerPlugin):
    name = "test_plugin"

    def __init__(self):
        self.redis = Redis(
            host="0.0.0.0",
            port=6379,
            db=0
        )

    def transition(self, key, start, finish, *args, **kwargs):
        print(f"{key}: {finish}")
        if start == "memory" and finish == "forgotten":
            finish = "done"

        self.redis.set(f"state-{key}", finish)

@click.command()
def dask_setup(scheduler):
    plugin = DaskWorkerPlugin()
    scheduler.add_plugin(plugin)
