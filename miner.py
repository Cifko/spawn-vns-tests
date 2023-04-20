# type:ignore

from config import NETWORK, REDIRECT_MINER_STDOUT, USE_BINARY_EXECUTABLE
import subprocess


class Miner:
    def __init__(self, base_node_grpc_port, wallet_grpc_port):
        if USE_BINARY_EXECUTABLE:
            run = "tari_miner"
        else:
            run = " ".join(["cargo", "run", "--bin", "tari_miner", "--manifest-path", "../tari/Cargo.toml", "--"])
        self.exec = " ".join(
            [
                run,
                "-b",
                "miner",
                "--network",
                NETWORK,
                "--max-blocks",
                "#blocks",
                "-p",
                f"miner.base_node_grpc_address=/ip4/127.0.0.1/tcp/{base_node_grpc_port}",
                "-p",
                f"miner.wallet_grpc_address=/ip4/127.0.0.1/tcp/{wallet_grpc_port}",
                "-p",
                f"miner.num_mining_threads=1",
            ]
        )

    def mine(self, blocks):
        if REDIRECT_MINER_STDOUT:
            self.process = subprocess.call(self.exec.replace("#blocks", str(blocks)), stdout=open("stdout/miner_stdout.log", "a+"))
        else:
            self.process = subprocess.call(self.exec.replace("#blocks", str(blocks)))
