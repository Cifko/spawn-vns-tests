# type:ignore
from config import REDIRECT_DAN_WALLET_WEBUI_STDOUT
from ports import ports
import os
import platform
import subprocess
import signal
from common_exec import CommonExec


class TariConnectorSample(CommonExec):
    def __init__(self, signaling_server_address):
        super().__init__("connector-sample")
        if platform.system() == "Windows":
            npm = "npm.cmd"
        else:
            npm = "npm"
        self.http_port = self.get_port("HTTP")

        # first do npm install in tari-connector repo
        self.process = subprocess.call(
            f"{npm} install",
            stdin=subprocess.PIPE,
            stdout=open(f"stdout/tari-connector_prepare.log", "a+"),
            stderr=subprocess.STDOUT,
            cwd="../tari-connector",
        )

        # create tari-connector link
        self.process = subprocess.call(
            f"{npm} link",
            stdin=subprocess.PIPE,
            stdout=open(f"stdout/tari-connector_prepare.log", "a+"),
            stderr=subprocess.STDOUT,
            cwd="../tari-connector",
        )
        # install everything
        self.process = subprocess.call(
            f"{npm} install",
            stdin=subprocess.PIPE,
            stdout=open(f"stdout/tari-connector_prepare.log", "a+"),
            stderr=subprocess.STDOUT,
            cwd="../tari-connector/examples/material-vite-ts",
        )
        # link tari-connector package
        self.process = subprocess.call(
            f"{npm} link tari-connector",
            stdin=subprocess.PIPE,
            stdout=open(f"stdout/tari-connector_prepare.log", "a+"),
            stderr=subprocess.STDOUT,
            cwd="../tari-connector/examples/material-vite-ts",
        )
        # run the project
        self.exec = " ".join([npm, "run", "dev", "--", "--port", str(self.http_port)])
        self.env["VITE_SIGNALING_SERVER_ADDRESS"] = signaling_server_address
        self.run(
            REDIRECT_DAN_WALLET_WEBUI_STDOUT,
            "../tari-connector/examples/material-vite-ts",
        )
