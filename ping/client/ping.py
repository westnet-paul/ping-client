from dotenv import load_dotenv
import ipaddr
import os
import requests


load_dotenv()


class PingError(Exception):
    pass


class BasePing(object):
    """
    Not intended for client use. Abstracts out the task of getting the ping
    server's URL from the environment.
    """

    def __init__(self):

        self._server = os.environ.get("PING_SERVER_URL")
        if not self._server:
            raise PingError("The SERVER environment variable must be set")


class Ping(BasePing):
    """
    Leverage the ping-service k8s deployment to ping an IP address.

    Normal usage is to create a Ping instance and then check its `alive` and/or
    `rtt` properties. Accessing either for the first time will run a ping, the
    results of which will be cached. To ping the same address again, call the
    `ping` method.

    The `address` argument can be a string representing an IPv4 or IPv6 address,
    an IPv4Address, an IPv6Address, or a host name.
    """

    def __init__(self, address, ip=None, alive=None, rtt=None):
        """
        The `ip`, `alive` and `rtt` arguments are for the `NetPing` class to use
        when initialising pre-populated Ping instances. In normal usage, pass in
        an IPv4 or IPv6 address or hostname to the `address` parameter and leave
        the rest alone.
        """

        super(__class__, self).__init__()

        self.address = address
        self._ip = ip
        self._alive = alive
        self._rtt = rtt

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.address)

    def __str__(self):
        if self._alive is None:
            return "{}: pending".format(self.address)
        if self._alive:
            return "{}: {}".format(self.address, self._rtt)
        return "{}: -".format(self.address)

    def ping(self):
        r = requests.get("{}/{}".format(self._server, self.address)).json()
        if "alive" not in r:
            raise PingError(r.get("detail"))
        self._ip = r.get("address")
        self._alive = r.get("alive")
        self._rtt = r.get("rtt")

    @property
    def ip(self):
        if self._ip is None:
            self.ping()
        return self._ip

    @property
    def alive(self):
        if self._alive is None:
            self.ping()
        return self._alive

    @property
    def rtt(self):
        if self._alive is None:
            self.ping()
        return self._rtt


class NetPing(BasePing):
    """
    Given a CIDR subnet, create a sequence of Ping objects, each of which
    behaves as if it had been ping()ed individually.
    """

    def __init__(self, network):
        """
        The `network` can be either an IPv4Network instance or a string that
        can be interpreted as one.
        """

        super(__class__, self).__init__()

        try:
            self.network = ipaddr.IPv4Network(network)
        except ipaddr.AddressValueError as e:
            raise PingError(str(e))

        self._from_ip = str(network[0])
        self._to_ip = str(network[-1])
        self._pings = []
        self.ping()

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.network)

    def ping(self):
        r = requests.get("{}/network/{}".format(self._server, self.network)).json()
        self._pings = [
            Ping(address=h["address"], ip=h["address"], alive=h["alive"], rtt=h["rtt"])
            for h in r["hosts"]
        ]

    def __iter__(self):
        return iter(self._pings)

    def __len__(self):
        return len(self._pings)

    def __getitem__(self, index):
        return self._pings[index]
