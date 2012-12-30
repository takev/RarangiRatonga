
from datetime import datetime

class Dispatcher (object):
    def __init__(self, fd):
        self.fd = fd

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

    def timer(self):
        """Return the time and date when the select call should timeout.
        """
        return datetime.max

    def handle_read(self):
        """Handle a read event.
        The select call has found that there is data in the read buffer.
        """
        raise NotImplementedError("handle_read")

    def handle_write(self):
        """Handle a write event.
        The select call has found that there is room for data in the write buffer.
        """
        raise NotImplementedError("handle_write")

    def handle_exception(self):
        """Handle a exception event.
        The select call has found that something exceptionable is happening.
        """
        raise NotImplementedError("handle_exception")

    def handle_timer(self):
        """Handle a timer event.
        The select call has timed-out and the main loop is found this instance to be handling it.
        """
        raise NotImplementedError("handle_timer")

    def handle_close(self):
        """The connection must be closed.
        This function should be called by subclass to close the connection and remove it from the main loop.
        """
        if hasattr(self, "main_loop"):
            self.main_loop.remove(self)
            self.fd.close()

