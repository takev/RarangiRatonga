
import socket
from utils import split_lines_and_words, join_lines_and_words

class Buffer (object):
    def __init__(self, size):
        self.size = size
        self.inner = bytearray(self.size)
        self.length = 0

    def __len__(self):
        return self.length

    def __repr__(self):
        return "<Buffer %s>" % (self.inner[:self.length])

    def append_view(self):
        return memoryview(self.inner)[self.length:]

    def append(self, data):
        assert len(data) <= self.space()
        self.inner[self.length:self.length + len(data)] = data
        self.length+= len(data)

    def advance(self, offset):
        assert offset <= self.length, (offset, self.length)
        self.length-= offset
        self.inner[:self.length] = self.inner[offset:offset+self.length]

    def empty(self):
        return self.length == 0

    def full(self):
        return self.length == self.size

    def space(self):
        return self.size - self.length

    def recv_into(self, fd):
        received = fd.recv_into(self.append_view(), self.space())
        self.length+= received
        return received

    def send_outoff(self, fd):
        try:
            sent = fd.send(memoryview(self.inner)[:self.length])
        except socket.error:
            sent = 0

        self.advance(sent)
        print(self.length)
        return sent

    def get_lines_and_words(self):
        next_offset = 0
        for next_offset, line in split_lines_and_words(memoryview(self.inner)[:self.length]):
            print(next_offset, line)
            yield line

        self.advance(next_offset)

    def add_lines_with_words(self, lines):
        offset = join_lines_and_words(self, lines)
        print("lines:", lines, offset)
        del lines[:offset+1]
        print("lines2:", lines)

