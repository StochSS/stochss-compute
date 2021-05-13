from stochss_compute.api import base

def server_start():
    base.flask.run(host="0.0.0.0", port=1234)

if __name__ == "__main__":
    server_start()