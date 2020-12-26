import time

from . import exc


class Server(object):
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = int(port)

    def as_tuple(self):
        return (self.hostname, self.port)

    def __hash__(self):
        return hash(self.as_tuple())

    def __lt__(self, other): return self.as_tuple() <  other
    def __le__(self, other): return self.as_tuple() <= other
    def __eq__(self, other): return self.as_tuple() == other
    def __ne__(self, other): return self.as_tuple() != other
    def __gt__(self, other): return self.as_tuple() >  other
    def __ge__(self, other): return self.as_tuple() >= other

    def __repr__(self):
        return "Server({}, {}, {})".format(self.hostname, self.port)
