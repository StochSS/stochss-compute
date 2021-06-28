from stochss_compute.api import flask

def server_start():
    flask.run(host="0.0.0.0", port=1236, debug=True)

if __name__ == "__main__":
    server_start()