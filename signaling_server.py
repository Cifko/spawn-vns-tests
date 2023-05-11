# type:ignore
import os
import subprocess
import time
from ports import ports
from config import USE_BINARY_EXECUTABLE, REDIRECT_SIGNALING_STDOUT


class SignalingServer:
    def __init__(self):
        self.json_rpc_port = ports.get_free_port("Signaling server")
        if USE_BINARY_EXECUTABLE:
            run = "tari_signaling_server"
        else:
            run = " ".join(["cargo", "run", "--bin", "tari_signaling_server", "--manifest-path", "../tari-dan/Cargo.toml", "--"])
        self.exec = " ".join(
            [
                run,
                "-b",
                "signaling_server",
                "--listen-addr",
                f"127.0.0.1:{self.json_rpc_port}",
            ]
        )
        if REDIRECT_SIGNALING_STDOUT:
            self.process = subprocess.Popen(self.exec, stdout=open(f"stdout/signaling.log", "a+"), stderr=subprocess.STDOUT)
        else:
            self.process = subprocess.Popen(self.exec)
        # jrpc_address = f"http://127.0.0.1:{self.json_rpc_port}"
        # self.jrpc_client = JrpcDanWalletDaemon(jrpc_address)
        # self.http_client = DanWalletUI(self.id, jrpc_address)
        while not os.path.exists("signaling_server/pid"):
            print("waiting for signaling server to start")
            time.sleep(1)

    def __del__(self):
        self.process.kill()
