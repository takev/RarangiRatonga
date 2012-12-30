
from Dispatcher import Dispatcher

class ServerSocketDispatcher (Dispatcher):
    def __init__(self, fd, conn_cls):
        Dispatcher.__init__(self, fd)
        self.conn_cls = conn_cls

    def readable(self):
        return True

    def writeable(self):
        return False

    def handle_read(self):
        (new_fd, new_addr) = self.fd.accept()
        new_dispatcher = self.conn_cls(new_fd)
        self.main_loop.add(new_dispatcher)

    def handle_close(self):
        Dispatcher.handle_close(self)

