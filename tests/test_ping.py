import os
from ping import Ping, PingError
import pytest


TEST_URL = "http://py.test"


def test_ping_noenv():

    os.environ.pop("PING_SERVER_URL")
    with pytest.raises(PingError):
        _ = Ping("1.1.1.1")


def test_ping_env():

    address = "1.1.1.1"

    os.environ["PING_SERVER_URL"] = TEST_URL
    instance = Ping(address)

    assert instance
    assert str(instance) == f"{address}: pending"
    assert repr(instance) == f"<Ping: {address}>"


def test_alive(requests_mock):

    address = "1.2.3.4"

    requests_mock.get(
        f"{TEST_URL}/{address}",
        json={"address": address, "alive": True, "rtt": 1.23},
    )
    os.environ["PING_SERVER_URL"] = TEST_URL
    instance = Ping(address)

    assert instance.rtt > 0
    assert instance.address == address
    assert instance.alive

    assert str(instance) == f"{address}: {instance.rtt}"


def test_dead(requests_mock):

    address = "9.8.7.6"

    requests_mock.get(
        f"{TEST_URL}/{address}",
        json={"address": address, "alive": False},
    )
    os.environ["PING_SERVER_URL"] = TEST_URL
    instance = Ping(address)

    assert not instance.alive
    assert instance.address == address
    assert str(instance) == f"{address}: -"


def test_dns(requests_mock):

    address = "example.com"
    ip = "10.20.30.40"

    requests_mock.get(
        f"{TEST_URL}/{address}",
        json={"address": ip, "alive": True, "rtt": 10.5},
    )
    os.environ["PING_SERVER_URL"] = TEST_URL
    instance = Ping(address)

    assert instance.address == address
    assert instance.ip == ip
    assert instance.alive
    assert str(instance) == f"{address}: {instance.rtt}"


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
