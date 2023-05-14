# type:ignore

from ports import ports
from config import NETWORK, REDIRECT_VN_FROM_INDEX_STDOUT, NO_FEES, USE_BINARY_EXECUTABLE
import subprocess
import os
import time
import re
import requests
from common_exec import CommonExec


class JrpcValidatorNode:
    def __init__(self, jrpc_url):
        self.id = 0
        self.url = jrpc_url
        self.token = None

    def internal_call(self, method, params=[]):
        self.id += 1
        response = requests.post(self.url, json={"jsonrpc": "2.0", "method": method, "id": self.id, "params": params})
        return response.json()["result"]

    def call(self, method, params=[]):
        return self.internal_call(method, params)

    def get_epoch_manager_stats(self):
        return self.call("get_epoch_manager_stats")


class ValidatorNode(CommonExec):
    def __init__(self, base_node_grpc_port, wallet_grpc_port, node_id, peers=[]):
        super().__init__("Validator_node", node_id)
        self.public_port = self.get_port("public_address")
        self.public_adress = f"/ip4/127.0.0.1/tcp/{self.public_port}"
        self.json_rpc_port = self.get_port("JRPC")
        self.json_rpc_address = f"127.0.0.1:{self.json_rpc_port}"
        self.http_port = self.get_port("HTTP")
        self.http_ui_address = f"127.0.0.1:{self.http_port}"
        if USE_BINARY_EXECUTABLE:
            run = "tari_validator_node"
        else:
            run = " ".join(["cargo", "run", "--bin", "tari_validator_node", "--manifest-path", "../tari-dan/Cargo.toml", "--"])
        self.exec = " ".join(
            [
                run,
                "-b",
                f"vn{node_id}",
                "--network",
                NETWORK,
                "-p",
                f"validator_node.base_node_grpc_address=127.0.0.1:{base_node_grpc_port}",
                "-p",
                f"validator_node.wallet_grpc_address=127.0.0.1:{wallet_grpc_port}",
                "-p",
                "validator_node.p2p.transport.type=tcp",
                "-p",
                f"validator_node.p2p.transport.tcp.listener_address={self.public_adress}",
                "-p",
                "validator_node.p2p.allow_test_addresses=true",
                "-p",
                f"{NETWORK}.p2p.seeds.peer_seeds={','.join(peers)}",
                # "-p",
                # f"validator_node.p2p.public_address={self.public_adress}",
                "-p",
                f"validator_node.public_address={self.public_adress}",
                "-p",
                f"validator_node.json_rpc_address={self.json_rpc_address}",
                "-p",
                f"validator_node.http_ui_address={self.http_ui_address}",
                "-p",
                f"validator_node.no_fees={NO_FEES}",
            ]
        )
        self.run(REDIRECT_VN_FROM_INDEX_STDOUT)
        # while not os.path.exists(f"vn{node_id}/localnet/pid"):
        #     print("Waiting for VN to start")
        #     if self.process.poll() is None:
        #         time.sleep(1)
        #     else:
        #         raise Exception(
        #             f"Indexer did not start successfully: Exit code:{self.process.poll()}")
        self.jrpc_client = JrpcValidatorNode(f"http://127.0.0.1:{self.json_rpc_port}")

    def get_address(self):
        validator_node_id_file_name = f"./vn{self.id}/{NETWORK}/validator_node_id.json"
        while not os.path.exists(validator_node_id_file_name):
            time.sleep(0.3)
        f = open(validator_node_id_file_name, "rt")
        content = "".join(f.readlines())
        node_id, public_key, public_address = re.search(
            r'"node_id":"(.*?)","public_key":"(.*?)".*"public_addresses":\["(.*?)"', content
        ).groups()
        public_address = public_address.replace("\\/", "/")
        return f"{public_key}::{public_address}"

    def register(self):
        if USE_BINARY_EXECUTABLE:
            run = "tari_validator_node_cli"
        else:
            run = " ".join(["cargo", "run", "--bin", "tari_validator_node_cli", "--manifest-path", "../tari-dan/Cargo.toml", "--"])
        self.exec_cli = " ".join([run, "--vn-daemon-jrpc-endpoint", f"/ip4/127.0.0.1/tcp/{self.json_rpc_port}", "vn", "register"])
        if self.id >= REDIRECT_VN_FROM_INDEX_STDOUT:
            self.cli_process = subprocess.call(self.exec_cli, stdout=open(f"stdout/vn_{self.id}_cli.log", "a+"), stderr=subprocess.STDOUT)
        else:
            self.cli_process = subprocess.call(self.exec_cli)
