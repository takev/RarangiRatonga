
import re
from StreamSocketDispatcher import StreamSocketDispatcher
from utils import findall, previous, last

class LineSocketDispatcher (StreamSocketDispatcher):
    def __init__(self, sock_family, sock_type, remote_address, fd=None):
        StreamSocketDispatcher.__init__(self, sock_family, sock_type, remote_address, fd)
        self.read_lines = []
        self.write_lines = []

    def writable(self):
        return StreamSocketDispatcher.writeable(self) or self.write_lines

    def handle_read(self):
        StreamSocketDispatcher.handle_read(self)

        for line in self.read_buffer.get_lines_and_words():
            self.read_lines.append(line)

        print("read line:", self.read_lines)

    def handle_write(self):
        print("write_lines:", self.write_lines)
        self.write_buffer.add_lines_with_words(self.write_lines)
        print("write_lines2:", self.write_lines)
        StreamSocketDispatcher.handle_write(self)

    def send(self, *words):
        self.write_lines.append(words)

