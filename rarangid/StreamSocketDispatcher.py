
import utils
import socket
from Dispatcher import Dispatcher
from Buffer import Buffer

class StreamSocketDispatcher (Dispatcher):
    def __init__(self, fd):
        Dispatcher.__init__(self, fd)
        self.read_buffer = Buffer(4096)
        self.write_buffer = Buffer(4096)
        try:
            self.uid = utils.get_peer_uid(fd)
            self.gids = utils.uid_gids.get(self.uid, [])
        except (OSError, socket.error):
            self.uid = None
            self.gids = set()

        print("uid:", self.uid, self.gids)

    def readable(self):
        return not self.read_buffer.full()

    def writeable(self):
        return not self.write_buffer.empty()

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

    def handle_close(self):
        self.fd.close()
        Dispatcher.handle_close(self)

