
from datetime import datetime
from select import select

class MainLoop (object):
    def __init__(self):
        self.dispatchers = set()

    def add(self, dispatcher):
        self.dispatchers.add(dispatcher)
        dispatcher.main_loop = self

    def remove(self, dispatcher):
        self.dispatchers.remove(dispatcher)
        del dispatcher.main_loop

    def iterate(self):
        readers = []
        writers = []
        exceptions = []
        timers = []

        # Build up lists of things to wait for.
        for dispatcher in self.dispatchers:
            if dispatcher.readable(): readers.append(dispatcher)
            if dispatcher.writable(): writers.append(dispatcher)
            if dispatcher.exceptionable(): exceptions.append(dispatcher)
            if dispatcher.timer() < datetime.max: timers.append(dispatcher)

        # Find out the next timeout moment for select.
        timers.sort(key=lambda x: x.timer())
        timeout = (next_timers[0].timer() - datetime.now()).total_seconds() if timers else 3600.0

        # Check which dispatcher should handle events.
        print("enter select")
        readers, writers, exceptions = select(readers, writers, exceptions, timeout)
        print("exit select")
        timers = [x for x in timers if x.timer() < datetime.now()]

        # Send events to each dispatcher that needs it.
        for reader in readers: reader.handle_read()
        for writer in writers: writer.handle_write()
        for exception in exceptions: exception.handle_exception()
        for timer in timers: timer.handle_timer()

    def loop(self):
        while self.dispatchers:
            self.iterate()
        

if __name__ == "__main__":
    pass

