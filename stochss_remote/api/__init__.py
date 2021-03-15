from flask import Flask
from stochss_remote.api.v1.job import blueprint

def server_start():
    app = Flask(__name__)
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.register_blueprint(blueprint)

    app.run()