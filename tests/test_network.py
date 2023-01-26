import ipaddr
import os
from ping import NetPing, PingError
import pytest


TEST_URL = "http://py.test"


def test_notanet():
    """
    A value that's not an address or CIDR should raise an error.
    """

    with pytest.raises(PingError):
        _ = NetPing("not.a.network")


def test_straddr(requests_mock):
    """
    A string representing an address should behave like a /32.
    """

    address = "1.2.3.4"
    requests_mock.get(
        f"{TEST_URL}/network/{address}/32",
        json={
            "hosts": [{"address": address, "ip": address, "alive": True, "rtt": 1.23}]
        },
    )

    os.environ["PING_SERVER_URL"] = TEST_URL
    instance = NetPing(address)
    assert repr(instance) == f"<NetPing: {address}/32>"
    assert len(instance) == 1
    assert instance[0].address == instance[0].ip == address


def test_ipaddr(requests_mock):
    """
    An IPv4Address should behave like a /32.
    """

    ip = "1.2.3.4"
    address = ipaddr.IPAddress(ip)
    requests_mock.get(
        f"{TEST_URL}/network/{ip}/32",
        json={"hosts": [{"address": ip, "ip": ip, "alive": True, "rtt": 1.23}]},
    )

    os.environ["PING_SERVER_URL"] = TEST_URL
    instance = NetPing("1.2.3.4")
    assert repr(instance) == f"<NetPing: {address}/32>"
    assert len(instance) == 1
    assert instance[0].address == instance[0].ip
    assert str(instance[0].ip) == ip


def test_strnetwork(requests_mock):
    """
    A string representing a subnet should behave like an IPv4Network.
    """

    network = "1.2.3.0/30"
    addresses = [f"1.2.3.{n}" for n in range(4)]
    requests_mock.get(
        f"{TEST_URL}/network/{network}",
        json={
            "hosts": [
                {"address": address, "ip": address, "alive": True, "rtt": 1.23}
                for address in addresses
            ]
        },
    )

    os.environ["PING_SERVER_URL"] = TEST_URL
    instance = NetPing(network)
    assert repr(instance) == f"<NetPing: {network}>"
    assert len(instance) == 4
    for ping, address in zip(instance, addresses):
        assert ping.address == ping.ip == address


def test_network(requests_mock):
    """
    An IPv4Network should Just Work.

    This tests a mix of alive/dead responses from the server also.
    """

    network = ipaddr.IPNetwork("1.2.3.0/30")
    addresses = list(zip([f"1.2.3.{n}" for n in range(4)], [False, True, True, False]))
    requests_mock.get(
        f"{TEST_URL}/network/{network}",
        json={
            "hosts": [
                {
                    "address": address[0],
                    "ip": address[0],
                    "alive": address[1],
                    "rtt": 1.23 if address[1] else None,
                }
                for address in addresses
            ]
        },
    )

    os.environ["PING_SERVER_URL"] = TEST_URL
    instance = NetPing(network)
    assert repr(instance) == f"<NetPing: {network}>"
    assert len(instance) == 4
    for ping, address in zip(instance, addresses):
        assert ping.address == ping.ip == address[0]
        assert ping.alive == address[1]
        if ping.alive:
            assert ping.rtt > 0
        else:
            assert ping.rtt is None
