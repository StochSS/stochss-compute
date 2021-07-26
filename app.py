from stochss_compute import api

def server_start():
    api.start_api(host="localhost", port=1234, debug=True)

if __name__ == "__main__":
    server_start()
