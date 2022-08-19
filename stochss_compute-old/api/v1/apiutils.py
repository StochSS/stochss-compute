from flask import g
from flask import current_app

from werkzeug.local import LocalProxy

from ..delegate import Delegate

def get_delegate():
    if "delegate" in g:
        return g.delegate

    delegate_config = current_app.config["DELEGATE_CONFIG"]
    delegate_type = current_app.config["DELEGATE_TYPE"]

    # # May be None
    # kube_cluster = current_app.config["KUBE_CLUSTER"]
    
    delegate = delegate_type(delegate_config)

    if False in (delegate.connect(), delegate.test_connection()):
        raise Exception("Delegate connection failed.")

    return delegate

delegate: Delegate = LocalProxy(get_delegate)
