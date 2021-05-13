from .factory import Factory

base = Factory()

base.set_flask()
base.set_celery()

flask = base.flask
celery = base.celery

from .v1 import blueprint as v1_api

base.register(v1_api)