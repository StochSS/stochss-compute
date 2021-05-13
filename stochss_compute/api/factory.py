import celery
from flask import Flask
from celery import Celery
from celery.utils.log import get_task_logger

from . import celery_config

class Factory(object):
    def __init__(self, environment="default"):
        self._environment = environment

    def set_flask(self, **kwargs):
        self.flask = Flask(__name__, **kwargs)
        self.flask.config.update(
            JSONFIY_PRETTYPRINT_REGULAR=True,
        )

        return self.flask

    def set_celery(self, **kwargs):
        self.celery = Celery("stochss-compute_celery", **kwargs)
        self.celery.config_from_object(celery_config)
        self.logger = get_task_logger(__name__)

        return self.celery

    def register(self, blueprint):
        self.flask.register_blueprint(blueprint)
