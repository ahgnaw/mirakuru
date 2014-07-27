"""HTTP Executor tests."""
import os
import sys
import pytest


HOST = "127.0.0.1"
PORT = "8000"


from mirakuru.compat import HTTPConnection, OK


if sys.version_info.major == 2:
    http_server = "SimpleHTTPServer"
else:
    http_server = "http.server"

from mirakuru import HTTPExecutor
from mirakuru import TimeoutExpired


def prepare_slow_server_executor(timeout=None):
    """
    Construct slow server executor.

    :param int timeout: executor timeout.
    :returns: executor instance
    :rtype: mirakuru.executor.HTTPExecutor
    """
    slow_server = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "../slow_server.py"
    )

    command = 'python {0}'.format(slow_server)

    return HTTPExecutor(
        command,
        'http://{0}:{1}/'.format(HOST, PORT),
        timeout=timeout,
    )


def test_executor_starts_and_waits():
    """Test if process awaits for HEAD request to be completed."""
    command = 'bash -c "sleep 3 && exec python -m {http_server}"'.format(
        http_server=http_server,
    )
    executor = HTTPExecutor(
        command, 'http://{0}:{1}/'.format(HOST, PORT),
        timeout=20
    )
    executor.start()
    assert executor.running() is True

    conn = HTTPConnection(HOST, PORT)
    conn.request('GET', '/')
    assert conn.getresponse().status is OK
    conn.close()

    executor.stop()


def test_slow_server_starting():
    """
    Test whether or not executor awaits for slow starting servers.

    Simple example. You run gunicorn, gunicorn is working
    but you have to wait for worker procesess.
    """
    executor = prepare_slow_server_executor()
    executor.start()
    assert executor.running() is True

    conn = HTTPConnection(HOST, PORT)
    conn.request('GET', '/')

    assert conn.getresponse().status is OK

    conn.close()
    executor.stop()


def test_slow_server_timeouted():
    """Check if timeout properly expires."""
    executor = prepare_slow_server_executor(timeout=1)

    with pytest.raises(TimeoutExpired):
        executor.start()

    assert executor.running() is False
