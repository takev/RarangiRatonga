"""Configuration file parser.
"""

import re
import utils
import sys

EXAMPLE_TEXT = """
    foo = no

    [hi]
    foo = 1
    bar = 2
    baz = 3

    [hello]
    foo = 1
    foo = ${hi:bar}
    bar = baz ; hello world
"""

class Section (object):
    def __init__(self, name):
        self.name = name
        self.pairs = {}

class Config (object):
    def __init__(self):
        self.sections = {}
        self.default_section = Section("DEFAULT")
        self.current_section = self.default_section

def parse(text):
    """Parse configuration file.

    >>> parse(EXAMPLE_TEXT)
    {'DEFAULT': [('foo', 'no')], 'hi': [('foo', '1'), ('bar', '2'), ('baz', '3')], 'hello': [('foo', '1'), ('foo', '${hi:bar}'), ('bar', 'baz')]}

    """
    current_section = 'DEFAULT'
    sections = {'DEFAULT': []}
    for line_nr, line in enumerate(text.split("\n")):
        line = utils.sanitize_string(line, comment_starts=['#', ';'])
        section_match = re.match(r'^\[([-.a-zA-Z0-9_]*)\]$', line)
        keyvalue_match = re.match(r'^([-.a-zA-Z0-9_]+)\s*=\s*(.*)$', line)

        if not line:
            continue

        elif section_match is not None:
            current_section = section_match.group(1)

        elif keyvalue_match is not None:
            section = sections.setdefault(current_section, [])
            section.append((keyvalue_match.group(1), keyvalue_match.group(2)))

        else:
            raise SyntaxError("No Section or key-value line at %i" % line_nr)

    return sections

def fixup_default(sections):
    """Add objects from the default section in all other sections.

    >>> s = parse(EXAMPLE_TEXT)
    >>> fixup_default(s)
    {'hi': [('foo', 'no'), ('foo', '1'), ('bar', '2'), ('baz', '3')], 'hello': [('foo', 'no'), ('foo', '1'), ('foo', '${hi:bar}'), ('bar', 'baz')]}
    """
    for keyvalues in {k:v for k, v in sections.items() if k != 'DEFAULT'}.values():
        keyvalues[:0] = sections['DEFAULT']

    del sections['DEFAULT']
    return sections

def fixup_arrays(sections, array_options=set()):
    """ Convert multiple values into an array.
    Single values are also put into a array with a single value for easy processing.

    >>> s = parse(EXAMPLE_TEXT)
    >>> s = fixup_default(s)
    >>> fixup_arrays(s, set(['foo']))
    {'hi': {'baz': ['3'], 'foo': ['no', '1'], 'bar': ['2']}, 'hello': {'foo': ['no', '1', '${hi:bar}'], 'bar': ['baz']}}
    """
    new_sections = {}
    for section_name, keyvalues in sections.items():
        new_section = new_sections.setdefault(section_name, {})
        for k, v in keyvalues:
            if k in array_options:
                new_section.setdefault(k, []).append(v)
            else:
                new_section[k] = [v]

    return new_sections


def fixup_placeholder(value, sections, current_section):
    l = re.split("\$\{(.*?)\}", value)
    new_l = []
    for i, x in enumerate(l):
        if (i % 2) == 0:
            new_l.append(x)
        else:
            if ":" in x:
                remote_section, x = x.split(":", 2)
                namespace = {k:v[-1] for k, v in sections[remote_section].items()}
            else:
                namespace = {k:v[-1] for k, v in sections[current_section].items()}

            new_value = namespace[x]
            if "${" in new_value:
                return None

            new_l.append(new_value)

    return "".join(new_l)


def fixup_placeholders(sections):
    """

    >>> fixup_placeholders({'hello': {'foo': ['1', '2'], 'bar': ['3']}, 'world': {'test': ['hello ${hello:foo} world'], 'bla': ['${test}']}})
    {'world': {'test': ['hello 2 world'], 'bla': ['hello 2 world']}, 'hello': {'foo': ['1', '2'], 'bar': ['3']}}
    """
    has_placeholders = True
    retry_count = 0
    while has_placeholders:
        if retry_count > 10:
            raise SyntaxError("Configuration file contains looping references.")

        has_placeholders = False
        for section_name, keyvalues in sections.items():
            for k, values in keyvalues.items():
                for i, value in enumerate(values):
                    new_value = fixup_placeholder(value, sections, section_name)
                    if new_value is None:
                        has_placeholders = True
                    else:
                        values[i] = new_value
        retry_count+= 1

    return sections


def fixup_types(_sections, types={}, array_options=set()):
    """Parse config file and fill in the blanks.
    """
    sections = parse_config(text)
    new_sections = {}
    for k, v in sections["DEFAULT"]:
        sections


if __name__ == "__main__":
    import doctest
    doctest.testmod()

