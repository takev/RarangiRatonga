
import utils
import socket
import sys
from Dispatcher import Dispatcher
from Buffer import Buffer

class StreamSocketDispatcher (Dispatcher):
    def __init__(self, sock_family, sock_type, remote_address, fd=None):
        Dispatcher.__init__(self, fd)
        self.sock_family = sock_family
        self.sock_type = sock_type
        self.remote_address = remote_address
        self.read_buffer = Buffer(4096)
        self.write_buffer = Buffer(4096)
        self.uid = None
        self.gids = set()

        # For AF_UNIX sockets find out the uid/gids of the caller.
        if self.fd is not None and self.sock_family == socket.AF_UNIX:
            self.uid = utils.get_peer_uid(fd)
            self.gids = utils.uid_gids.get(self.uid, [])

        # Connect if this is client side.
        if self.client:
            self.handle_connect()

        print("uid:", self.uid, self.gids)

    def readable(self):
        return not self.read_buffer.full()

    def writeable(self):
        return not self.write_buffer.empty()

    def handle_connect(self):
        Dispatcher.handle_connect(self)
        try:
            fd = socket.socket(self.sock_family, self.sock_type)
            fd.connect(self.remote_address)
            self.fd = fd
        except socket.error as e:
            print("ERROR could not open socket %s, %s" % (e, self), file=sys.stderr)

    def handle_read(self):
        received = self.read_buffer.recv_into(self.fd)
        if received == 0:
            print("read: close")
            self.handle_close()
        else:
            print("read:", self.read_buffer)

    def handle_write(self):
        sent = self.write_buffer.send_outoff(self.fd)
        if sent == 0:
            self.handle_close()

