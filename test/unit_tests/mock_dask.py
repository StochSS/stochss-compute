from distributed.utils_test import client, inc
import pytest

@pytest.fixture
def mock_dask(client, s, a, b):
    future = client.submit(inc, 10)
    assert future.result() == 11  # use the synchronous/blocking API here

    a['proc'].terminate()  # kill one of the workers

    result = future.result()  # test that future remains valid
    assert result == 2
    return (client, s, a, b)