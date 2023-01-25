import os
from ping import Ping, PingError
import pytest


TEST_URL = "http://py.test"


def test_ping_noenv():

    with pytest.raises(PingError):
        _ = Ping("1.1.1.1")


def test_ping_env():

    os.environ["PING_SERVER_URL"] = TEST_URL
    instance = Ping("1.1.1.1")

    assert instance


def test_alive(requests_mock):

    address = "1.2.3.4"

    requests_mock.get(
        f"{TEST_URL}/{address}",
        json={"address": address, "alive": True, "rtt": 1.23},
    )
    os.environ["PING_SERVER_URL"] = TEST_URL
    instance = Ping(address)

    assert instance.address == address
    assert instance.alive
    assert instance.rtt == 1.23


def test_dead(requests_mock):

    address = "9.8.7.6"

    requests_mock.get(
        f"{TEST_URL}/{address}",
        json={"address": address, "alive": False},
    )
    os.environ["PING_SERVER_URL"] = TEST_URL
    instance = Ping(address)

    assert instance.address == address
    assert not instance.alive


def test_invalid(requests_mock):

    address = "not.a.domain"

    requests_mock.get(
        f"{TEST_URL}/{address}",
        status_code=404,
        json={"detail": f"The name '{address}' cannot be resolved"},
    )
    os.environ["PING_SERVER_URL"] = TEST_URL
    instance = Ping(address)

    with pytest.raises(PingError) as excinfo:
        _ = instance.alive
    assert "cannot be resolved" in str(excinfo.value)
