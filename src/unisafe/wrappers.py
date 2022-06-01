from __future__ import annotations

import io
from typing import Generator


def gen_to_stream(iterable: Generator[bytes], buffer_size=io.DEFAULT_BUFFER_SIZE) -> io.BufferedReader:
    """
    Lets you use an iterable (e.g. a generator) that yields byte-strings as a read-only
    input stream.

    The stream implements Python 3's newer I/O API (available in Python 2's io module).
    For efficiency, the stream is buffered.
    """

    class IterStream(io.RawIOBase):
        def __init__(self):
            self.leftover = None

        def readable(self):
            return True

        def readinto(self, b):
            try:
                length = len(b)  # We're supposed to return at most this much
                chunk = self.leftover or next(iterable)
                output, self.leftover = chunk[:length], chunk[length:]
                b[:len(output)] = output
                return len(output)
            except StopIteration:
                return 0  # indicate EOF

    return io.BufferedReader(IterStream(), buffer_size=buffer_size)


def gen_to_textio(iterable: Generator[bytes]) -> io.TextIOWrapper:
    wrapper = io.TextIOWrapper(gen_to_stream(iterable), encoding='utf-8',
                               line_buffering=True)
    return wrapper
