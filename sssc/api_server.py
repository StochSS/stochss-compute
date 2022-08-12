
import requests

from enum import Enum

from requests.exceptions import ConnectionError
from time import sleep



class Server:    
    def __init__(self) -> None:
        raise TypeError('Server cannot be instantiated directly. Must be RemoteServer or Cluster.')

    def post(self, endpoint: Endpoint, sub: str, request = None) -> requests.Response:

        url = f"{self.address}{self.endpoints[endpoint]}{sub}"

        print(f"[{type(request).__name__}] {url}")
        n_try = 1
        sec = 3
        while n_try <= 3:
            try:
                if request is None:
                    print(f"[POST] {url}")
                    return requests.post(url)
                return requests.post(url, json=request.__dict__)

            except ConnectionError as ce:
                print(f"Connection refused by server. Retrying in {sec} seconds....")
                sleep(sec)
                n_try += 1
                sec *= n_try
            
            except Exception as e:
                print(f"Unknown error: {e}. Retrying in {sec} seconds....")
                sleep(sec)
                n_try += 1
                sec *= n_try

