
"""options - All options with default values.

"""

import getopt
import sys
import os.path
import utils
import configparser
import socket
import re
from datetime import timedelta

config_path = "/etc/rarangi.ini"
version = "1.0"
verbose = False
foreground = False
show_usage = False

heartbeat_interval = timedelta.max
heartbeat_timeout = timedelta.max

catalogue = None
environment = None
listen = set()
connect = set()

OPTIONS = "hVvfdc:"
LONG_OPTIONS = [
    "help",
    "version",
    "verbose",
    "foreground",
    "config-path=",
]

USAGE_TEMPLATE = """Real-time service catalogue daemon

Usage:
    {bin_name} [OPTIONS ...] <catalogue>

If a long options shows an argument as mandatory, then it is mandatory
for the equivalent short option also. Similarly for optional arguments.

Options:
    -h, --help                          Display this help.
    -V, --version                       Output version information to stdout and exit.
    -f, --foreground                    Run the daemon in the foreground, and redirect log to stderr.
    -v, --verbose                       Have more verbose output
    -c, --config-path=<config path>     Set the path to the configuration file ({config_path})

"""

def usage(exit_code):
    global config_path

    fmt_params = {
        "bin_name": os.path.basename(sys.argv[0]),
        "config_path": config_path
    }
    print(fmt_params)
    print(USAGE_TEMPLATE.format(**fmt_params), file=sys.stderr)
    exit(exit_code)

def parse_address(item):
    if item.startswith("/"):
        unix_path = item
        return {(socket.AF_UNIX, unix_path)}

    if item.isdigit():
        port = int(item)
        return {
            (socket.AF_INET, ("0.0.0.0", port)),
            (socket.AF_INET6, ("::", port))
        }

    m = re.match(r"\[([0-9a-fA-F:]+)\]:([0-9]+)", item)
    if m is not None:
        ipv6_address = m.group(1)
        port = int(m.group(2))
        return {(socket.AF_INET6, (ipv6_address, port))}

    m = re.match(r"([0-9.]+):([0-9]+)", item)
    if m is not None:
        ipv4_address = m.group(1)
        port = int(m.group(2))
        return {(socket.AF_INET, (ipv4_address, port))}

    m = re.match(r"([-.a-zA-Z0-9]+):([0-9]+)", item)
    if m is not None:
        hostname = m.group(1)
        port = int(m.group(2))
        return {(f, (a[0], a[1])) for f, t, p, c, a in socket.getaddrinfo(hostname, port) if f in (socket.AF_INET, socket.AF_INET6)}

    raise SyntaxError("Could not parse address '%s'" % item)

def parse_config(config_path, catalogue):
    global address
    global cluster
    global environment
    global address
    global listen
    global connect
    global heartbeat_interval
    global heartbeat_timeout

    p = configparser.RawConfigParser()
    p.read(config_path)

    cluster      = utils.sanitize_string(p.get(catalogue, "cluster"))
    environment  = utils.sanitize_string(p.get(catalogue, "environment"))
    heartbeat_interval = timedelta(seconds=int(utils.sanitize_string(p.get(catalogue, "heartbeat_interval"))))
    heartbeat_timeout = timedelta(seconds=int(utils.sanitize_string(p.get(catalogue, "heartbeat_timeout"))))
    listen_list  = utils.sanitize_string(p.get(catalogue, "listen"))
    connect_list = utils.sanitize_string(p.get(catalogue, "connect"))

    for item in listen_list.split(" "):
        listen.update(parse_address(item))

    for item in connect_list.split(" "):
        connect.update(parse_address(item))

    print("listen:", listen)
    print("connect:", connect)

def parse_options(args):
    """Parse options.
    """

    global show_usage
    global catalogue
    global version
    global verbose
    global config_path

    try:
        opts, args = getopt.getopt(args, OPTIONS, LONG_OPTIONS)
    except getopt.GetoptError as e:
        print(e, file=sys.stderr)
        usage(2)

    for o, a in opts:
        if o in ("-h", "--help"):
            show_usage = True

        elif o in ("-V", "--version"):
            print(version, file=sys.stdout)
            sys.exit(0)

        elif o in ("-v", "--verbose"):
            verbose = True

        elif o in ("-f", "--foreground"):
            foreground = True

        elif o in ("-c", "--config-path"):
            config_path = os.path.expanduser(utils.sanitize_string(a))

    # Parse mandatory arguments.
    if len(args) > 0:
        catalogue = utils.sanitize_string(args[0])
    if catalogue is None:
        print("ERROR: Expected mandatory catalogue name as argument", file=sys.stderr)
        usage(2)

    if show_usage:
        usage(0)

if __name__ == "__main__":
    parse_options(sys.argv[1:])
