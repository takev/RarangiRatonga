
import inspect
import options
from datetime import datetime
from LineSocketDispatcher import LineSocketDispatcher

class RarangiDispatcher (LineSocketDispatcher):
    def __init__(self, sock_family, sock_type, remote_address, fd=None):
        LineSocketDispatcher.__init__(self, sock_family, sock_type, remote_address, fd)
        self.heartbeat_sent = datetime.now()
        self.heartbeat_received = datetime.now()

    def timer(self):
        t1 = LineSocketDispatcher.timer(self)
        t2 = self.heartbeat_sent + options.heartbeat_interval
        t3 = self.heartbeat_received + options.heartbeat_timeout
        return min(t1, t2, t3)

    def handle_timer(self):
        if (datetime.now() >= self.heartbeat_sent + options.heartbeat_interval):
            self.send("HEARTBEAT")
            self.heartbeat_sent = datetime.now()

        if (datetime.now() >= self.heartbeat_received + options.heartbeat_timeout):
            self.handle_close()

        LineSocketDispatcher.handle_timer(self)

    def handle_command_HEARTBEAT(self):
        self.heartbeat_received = datetime.now()

    def handle_command_WELCOME(self, catalogue_name, cluster_name, environment_name):
        print("welcome", catalogue_name, cluster_name, environment_name)

    def handle_read(self):
        LineSocketDispatcher.handle_read(self)
        for line in self.read_lines:
            if not line:
                self.send("ERROR", "SYNTAX_ERROR")
                continue

            command = line[0].upper()
            arguments = line[1:]

            method_name = "handle_command_" + command

            if not hasattr(self, method_name):
                self.send("ERROR", "UNKNOWN_COMMAND", command)
                continue

            method = getattr(self, "handle_command_" + command)

            if not (len(inspect.getargspec(method).args) - 1) == len(arguments):
                self.send("ERROR", "EXPECT_ARGUMENTS", command, *inspect.getargspec(method).args[1:])
                continue

            method(*arguments)

        self.read_lines = []

    def handle_write(self):
        LineSocketDispatcher.handle_write(self)

    def handle_accept(self):
        self.send("WELCOME", options.catalogue, options.cluster, options.environment)
        LineSocketDispatcher.handle_accept(self)

