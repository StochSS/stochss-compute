# from stochss_compute.client.server import Server
# figure out type hinting for Server
from stochss_compute.client.endpoint import Endpoint
from gillespy2 import Results

from time import sleep

from tornado.escape import json_decode

class RemoteResults():

    def __init__(self, id, server, data = None):
        self.id = id
        self.server = server
        self._data = data

    # @property
    # def data(self):
    #     if self.local_data is None:
    #         print('Fetching Results.......')
    #         self.local_data = self.resolve().data
    #     return self.local_data


    def status(self):
        # Request the status of a running job.
        # pass
        # print(self.server)
        self.server.get(Endpoint.SIMULATION_GILLESPY2, f"/{self.id}/status")
        # if not status_response.ok:
        #     # TODO
        #     pass

        # status_response = json_decode(response_raw.text)

        # # Parse the body of the response into a JobStatusResponse object.
        # print(status.status_msg)
        # print(status.status_id)

        # return status.is_complete


    # def status(self) -> :
    #     """
    #     Get the status of the remote job.

    #     :returns: JobStatusResponse
    #     """

    #     status_response = self.server.get(Endpoint.JOB, f"/{self.result_id}/status")
    #     status: JobStatusResponse = unwrap_or_err(JobStatusResponse, status_response)

    #     return status


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

    # def cancel(self):
    #     """
    #     Cancels the remote job.
    #     """
    #     stop_response = self.server.post(Endpoint.JOB, f"/{self.result_id}/stop")

