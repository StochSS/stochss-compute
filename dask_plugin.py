import click

from redis import Redis
from distributed.diagnostics.plugin import SchedulerPlugin

from stochss_compute.api.delegate import DaskDelegateConfig

class DaskWorkerPlugin(SchedulerPlugin):
    name = "test_plugin"

    def __init__(self, redis_address, redis_port, redis_db):
        self.redis = Redis(
            host=redis_address,
            port=redis_port,
            db=redis_db
        )

    def transition(self, key, start, finish, *args, **kwargs):
        print(f"{key}: {finish}")
        if start == "memory" and finish == "forgotten":
            finish = "done"

        self.redis.set(f"state-{key}", finish)

@click.command()
def dask_setup(scheduler):
    config = DaskDelegateConfig()

    plugin = DaskWorkerPlugin(config.redis_address, config.redis_port, config.redis_db)
    scheduler.add_plugin(plugin)
