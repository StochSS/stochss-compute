# from stochss_compute.client.server import Server
# figure out type hinting for Server
from stochss_compute.client.endpoint import Endpoint
from gillespy2 import Results

from time import sleep

from tornado.escape import json_decode
from stochss_compute.core.errors import RemoteSimulationError

from stochss_compute.core.messages import SimStatus, StatusResponse

class RemoteResults(Results):

    id = None
    server = None

    def __init__(self, data = None):

        self._data = data

    @property
    def data(self):
        if self.id is None or self.server is None:
            raise Exception('RemoteResults must have a self.id and a self.server.')

            
        self._resolve()
        return self._data


    def _status(self):
        # Request the status of a running job.
        response_raw = self.server.get(Endpoint.SIMULATION_GILLESPY2, f"/{self.id}/status")
        if not response_raw.ok:
            raise Exception(response_raw.reason)

        status_response = StatusResponse.parse(response_raw.text)
        print(status_response.status)
        print(status_response.error_message)
        # # Parse the body of the response into a JobStatusResponse object.
        # print(status.status_msg)
        # print(status.status_id)
        return status_response

    def _resolve(self):
        if self.data is None:
            status = self._status()
            if status == SimStatus.PENDING:
                print('Simulation is pending (not running yet). Checking for status update....')
                while True:
                    sleep(5)
                    status = self._status()
                    if status != SimStatus.PENDING:
                        break
            if status == SimStatus.RUNNING:
                print('Simulation is running. Downloading results when complete......')
                while True:
                    sleep(5)
                    status = self._status()
                    if status == SimStatus.PENDING:
                        raise Exception('Unknown Error.')
                    if status != SimStatus.RUNNING:
                        break
            if status == SimStatus.READY:
                print('Results ready. Fetching.......')
            if status == SimStatus.ERROR:
                raise RemoteSimulationError(status.error_message)

        response_raw = self.server.get(Endpoint.SIMULATION_GILLESPY2, f"/{self.id}/results")
        if not response_raw.ok:
            raise Exception(response_raw.reason)

    def ready(self):
        return self._status().status == SimStatus.READY

    def error(self):
        status_response = self._status()
        # raise error by grabbing error class from task and put into response object


    # def resolve(self) -> Results:
    #     """
    #     Finish the remote job and return the results.
    #     This function will block until the remote job is complete.

    #     :returns: Results
    #     """

    #     # Poll the job status until it finishes.
    #     while not self.__poll_job_status():
    #         sleep(5)

    #     # Request the results of the finished job.
    #     results_response = self.server.get(Endpoint.RESULT, f"/{self.result_id}/get")

    #     if not results_response.ok:
    #         raise Exception(ErrorResponse.parse_raw(results_response.text).msg)

    #     print(f"Results size: {sys.getsizeof(results_response.content)}")
    #     results_json = bz2.decompress(results_response.content).decode()
    #     print(f"Expanded to: {sys.getsizeof(results_json)}")

    #     # Parse and return the response body into a valid Results object.
    #     results = Results.from_json(results_json)

    #     return results

    def cancel(self):
        """
        Cancels the remote job.
        """
        stop_response = self.server.post(Endpoint.JOB, f"/{self.result_id}/stop")

