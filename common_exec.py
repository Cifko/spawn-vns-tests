import os
import signal
import subprocess
from ports import ports
from typing import Optional, Any


class CommonExec:
    def __init__(self, name: str, id: Optional[int] = None):
        self.env: dict[str, str] = {}
        self.id = id
        if id:
            self.name = f"{name}_{id}"
        else:
            self.name = name
        self.exec = ""
        self.process: Optional[subprocess.Popen[Any]] = None

    def get_port(self, interface: str) -> int:
        return ports.get_free_port(f"{self.name} {interface}")

    def run(self, redirect: bool | int, cwd: Optional[str] = None):
        env: dict[str, str] = os.environ.copy()
        if (self.id and self.id >= redirect) or (not self.id and redirect):
            self.process = subprocess.Popen(
                self.exec,
                stdin=subprocess.PIPE,
                stdout=open(f"stdout/{self.name}.log", "a+"),
                stderr=subprocess.STDOUT,
                env={**env, **self.env},
                cwd=cwd,
            )
        else:
            self.process = subprocess.Popen(self.exec, stdin=subprocess.PIPE, env={**env, **self.env}, cwd=cwd)

    def __del__(self):
        print(f"kill {self.name}")
        print(f"To run {self.exec}", end=" ")
        if self.env:
            print(f"With env {self.env}", end="")
        print()
        try:
            if self.process:
                os.kill(self.process.pid, signal.CTRL_C_EVENT)
        except:
            pass
        del self.process
