"""Utility functions.
"""

import platform
import struct
import pwd
import grp

uid_gids = {}
uname_uid = {}
gname_gid = {}

def init():
    for user in pwd.getpwall():
        uname_uid[user.pw_name] = user.pw_uid
        uid_gids.setdefault(user.pw_uid, set()).add(user.pw_gid)

    for group in grp.getgrall():
        gname_gid[group.gr_name] = group.gr_gid
        for gr_mem in group.gr_mem:
            try:
                uid = uname_uid[gr_mem]
                uid_gids.setdefault(uid, set()).add(group.gr_gid)
            except KeyError:
                pass


def get_peer_uid(fd):
    """Return the peer's user id on a UNIX domain socket.
    """
    system = platform.system().lower()

    if system in ('linux'):
        SO_PEERCRED = 17

        cred_fmt = "3i"
        pid, uid, gid = struct.unpack(cred_fmt, fd.getsockopt(SOL_SOCKET, SO_PEERCRED, struct.calcsize(cred_fmt)))
        return uid
    
    elif system in ('darwin'):
        LOCAL_PEERCRED = 0x001

        cred_fmt = '3i16i'
        data_size = struct.calcsize(cred_fmt)
        data = fd.getsockopt(0, LOCAL_PEERCRED, data_size)
        if len(data) != data_size:
            raise OSError("Size of data returned (%i) from getsockopt is different from expected (%i)" % (len(data), data_size))

        res = struct.unpack(cred_fmt, data)
            
        # Check this is the above version of the structure
        if res[0] != 0:
            raise OSError("Unknown structure version %i" % (res[0]))

        return res[1]
    else:
        raise NotImplementedError("Unknown system %s" % (system))


def string_join(l, encoding='UTF-8'):
    r"""Try to join a list of characters.
    
    >>> string_join([56, 57, 58])
    '89:'

    >>> string_join(['h', 'o', 'i'])
    'hoi'

    >>> string_join([b'h', b'o', b'i'])
    'hoi'

    """
    if not l:
        return ""
    if isinstance(l[0], str):
        return "".join(l)
    if isinstance(l[0], bytes):
        return b"".join(l).decode(encoding)
    if isinstance(l[0], int):
        return bytes(l).decode(encoding)
    raise TypeError("Unknown type %s" % type(l[0]))

def join_lines_and_words(buf, lines):
    i = 0
    for i, line in enumerate(lines):
        new_line = []
        for word in line:
            new_word = []
            for c in word:
                if c == '\r':
                    continue

                elif c in ('\n', ' ', '\\'):
                    new_word.append('\\')

                new_word.append(c)
            new_line.append("".join(new_word).encode('UTF-8'))

        line = b" ".join(new_line) + b'\n'
        if buf.space() < len(line):
            # The line doesn't fit, so return the line that didn't fit.
            return i

        buf.append(line)
    return i

def split_lines_and_words(text):
    r"""Return a iterator of lines, each is a list of words, with the character index of the next line.
    This function is normally used on received data, therefor only complete lines are UTF-8 decoded.

    >>> [x for x in split_lines_and_words(memoryview(bytearray(b'Hello World\nMerry\\ Christmas\\\\ Everyone\\\r\nHow are you\nLast line')))]
    [(12, ['Hello', 'World']), (54, ['Merry Christmas\\', 'Everyone\nHow', 'are', 'you'])]
    """
    words = []
    word = []
    escape = False
    for i, c in enumerate(text):
        if c in (13, b'\r', '\r'):
            # All carriage returns are ignored, even when escaped; it doesn't reset escape either.
            pass
        elif escape:                    
            # A character after an escape character is always passed on.
            word.append(c)
            escape = False
        elif c in (92, b'\\', '\\'):
            # A backslash starts an escape sequence.
            escape = True
        elif c in (32, b' ', ' '):
            # A space separates a word.
            try:
                words.append(string_join(word))
            except UnicodeDecodeError:
                pass
            word = []
        elif c in (10, b'\n', '\n'):
            # A linefeed separates a line.
            try:
                words.append(string_join(word))
            except UnicodeDecodeError:
                pass

            yield i + 1, words
            word = []
            words = []
        else:
            word.append(c)

def last(iterator):
    """Return an iterator with a last flag and original of an iterator.

    >>> [x for x in last([1, 2, 3])]
    [(False, 1), (False, 2), (True, 3)]

    >>> [x for x in last([1])]
    [(True, 1)]

    >>> [x for x in last([])]
    []

    """
    first_time = True
    for i in iterator:
        if first_time:
            first_time = False
        else:
            yield (False, p)
        p = i

    else:
        if not first_time:
            yield (True, p)

def previous(iterator, previous = None):
    """Return an iterator with a previous and original of an interator.

    >>> [x for x in previous([2, 3, 4, 5])]
    [(None, 2), (2, 3), (3, 4), (4, 5)]
    """
    for i in iterator:
        yield (previous, i)
        previous = i

def findall(haystack, needle):
    r"""Return all the indices of non-overlapping needles in haystack.

    >>> findall('Merry Christmas everyone.', ' ')
    [5, 15]
    """
    f = []
    i = 0
    while i < len(haystack):
        found_at = haystack.find(needle, i)
        if found_at == -1:
            break

        f.append(found_at)
        i+= (found_at + len(needle))
    return f

def sanitize_string(s, space_character=" ", comment_starts=[]):
    r"""Return a sanitized version of the passed string.

    This function removes non-printable characters and leading & trailing white spaces.
    It also replaces all continues strings of white spaces with a single space_character.

    Parameters:
    s               - String to be sanitized.
    space_character - The character to use as a space character after sanitation.

    >>> sanitize_string("  hello \n  world ")
    'hello world'

    >>> sanitize_string("  hello  world ", space_character="_")
    'hello_world'
    
    >>> sanitize_string("  hello  world ; foobar", space_character="_", comment_starts=["#", ";"])
    'hello_world'
    """

    # Remove comments at the end of the line.
    for comment_start in comment_starts:
        i = s.find(comment_start)
        if i >= 0:
            s = s[:i]

    # Strip leading and trailing whitepsace
    s = s.strip()

    # Remove all printable characters, and convert multiple white-spaces characters in a single space.
    t = []
    for c in s:
        if c.isspace():
            if t[-1] != space_character:    # because there is not leading white space -1 is always a character.
                t.append(space_character)

        elif c.isprintable():
            t.append(c)
    
    return "".join(t)


init()
if __name__ == "__main__":
    import doctest
    doctest.testmod()


