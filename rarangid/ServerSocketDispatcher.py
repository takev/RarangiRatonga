import socket
import os
from Dispatcher import Dispatcher

class ServerSocketDispatcher (Dispatcher):
    def __init__(self, sock_family, sock_type, bind_address, factory):
        Dispatcher.__init__(self)
        self.sock_family = sock_family
        self.sock_type = sock_type
        self.sock_type = sock_type
        self.bind_address = bind_address
        self.factory = factory


        if sock_family == socket.AF_UNIX:
            try: os.unlink(bind_address)
            except OSError: pass
            
        fd = socket.socket(self.sock_family, self.sock_type)
        fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        fd.bind(self.bind_address)
        fd.listen(5)
        self.fd = fd

    def readable(self):
        return True

    def handle_read(self):
        (new_fd, new_address) = self.fd.accept()
        new_dispatcher = self.factory(self.sock_family, self.sock_type, new_address, fd=new_fd)
        self.main_loop.add(new_dispatcher)

