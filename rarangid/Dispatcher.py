import sys
from datetime import datetime
import options

class Dispatcher (object):
    def __init__(self, fd=None):
        print("INFO: Add dispatcher: %s" % (self), file=sys.stderr)
        self.fd = fd
        self.client = fd is None
        self.server = not self.client
        self.auto_reconnect = True
        self.auto_reconnect_last = datetime.now()

    def reset(self):
        self.auto_reconnect_last = datetime.now()

    def connected(self):
        return self.fd is not None

    def fileno(self):
        """Return a file discriptor so an instance of Dispatcher can be used directly in a select call.
        """
        return self.fd.fileno()

    def readable(self):
        """Return True if this Dispatcher instance should be passed in the select call.
        """
        return False

    def writable(self):
        """Return True if this Dispatcher instance should be passed in the select call.
        """
        return False

    def exceptionable(self):
        """Return True if this Dispatcher instance should be passed in the select call.
        """
        return False

    def need_to_reconnect(self):
        return self.client and not self.connected() and self.auto_reconnect

    def timer(self):
        """Return the time and date when the select call should timeout.
        """
        if self.need_to_reconnect():
            return self.auto_reconnect_last + options.reconnect_interval
        else:
            return datetime.max

    def handle_read(self):
        """Handle a read event.
        The select call has found that there is data in the read buffer.
        """

    def handle_write(self):
        """Handle a write event.
        The select call has found that there is room for data in the write buffer.
        """

    def handle_exception(self):
        """Handle a exception event.
        The select call has found that something exceptionable is happening.
        """

    def handle_accept(self):
        """Handle a connection event.
        """
        self.reset()

    def handle_connect(self):
        """Handle a connection event.
        """
        self.auto_reconnect_last = datetime.now()
        self.reset()

    def handle_timer(self):
        """Handle a timer event.
        The select call has timed-out and the main loop is found this instance to be handling it.
        """
        if self.need_to_reconnect() and (datetime.now() >= self.auto_reconnect_last + options.reconnect_interval):
            self.handle_connect()

    def handle_close(self):
        """The connection must be closed.
        This function should be called by subclass to close the connection and remove it from the main loop.
        """
        print("INFO: Handling close %s" % (self), file=sys.stderr)
        self.auto_reconnect_last = datetime.now()
        if hasattr(self, "main_loop"):
            if self.connected():
                print("INFO: Closing socket %s %s" % (repr(self.fd), self), file=sys.stderr)
                fd = self.fd
                self.fd = None
                fd.close()

            if not self.auto_reconnect:
                print("INFO: Removing dispatcher from main loop %s" % (self), file=sys.stderr)
                self.main_loop.remove(self)

