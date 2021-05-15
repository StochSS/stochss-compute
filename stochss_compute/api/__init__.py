from os import name
from stochss_compute.api.delegate.celery_delegate import CeleryDelegate, CeleryDelegateConfig
from stochss_compute.api.delegate.delegate import Delegate, DelegateConfig
from .factory import Factory
from . import celery_config

base = Factory()

base.set_flask()
# base.set_celery()

flask = base.flask
# celery = base.celery

delegate: Delegate = CeleryDelegate(CeleryDelegateConfig(name="stochss-compute_celery", celery_config=celery_config))

from .v1 import blueprint as v1_api

base.register(v1_api)