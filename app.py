from stochss_compute import api
import sys

def server_start(host="0.0.0.0", port=1234, debug=True):
    api.start_api(host=host, port=port, debug=debug)

if __name__ == "__main__":
    print(sys.argv)
    server_start()
