
import inspect
from LineSocketDispatcher import LineSocketDispatcher

class RarangiDispatcher (LineSocketDispatcher):
    def __init__(self, sock_family, sock_type, remote_address, fd=None):
        LineSocketDispatcher.__init__(self, sock_family, sock_type, remote_address, fd)

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


