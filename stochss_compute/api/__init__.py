try:
    import flask
except ImportError:
    pass
else:
    from .api import start_api