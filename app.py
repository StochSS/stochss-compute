from stochss_compute import api

def server_start():
    api.start_api(host="0.0.0.0", port=1234, debug=False)

if __name__ == "__main__":
    server_start()
