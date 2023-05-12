# type:ignore
import socket, errno
import sys


def is_port_used(port):
    sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sck.bind(("127.0.0.1", port))
    except socket.error as e:
        if e.errno != errno.EADDRINUSE:
            print(f"Some error on getting port usage {e}")
            sys.stdout.flush()
        return True
    sck.close()
    return False


class Ports:
    def __init__(self):
        self.last_used = 18003

    def get_free_port(self, name: str) -> int:
        self.last_used += 1
        while is_port_used(self.last_used):
            self.last_used += 1
        print(f"Port {self.last_used} has been assigned to {name}")
        sys.stdout.flush()
        return self.last_used


ports = Ports()
