# type:ignore

from config import NETWORK, REDIRECT_INDEXER_STDOUT, USE_BINARY_EXECUTABLE
from ports import ports
import os
import time
import re
import requests
import subprocess


class Indexer:

    def __init__(self, base_node_grpc_port, peers=[]):
        self.public_adress = f"/ip4/127.0.0.1/tcp/{ports.get_free_port()}"
        self.json_rpc_port = ports.get_free_port()
        self.json_rpc_address = f"127.0.0.1:{self.json_rpc_port}"
        self.http_ui_address = f"127.0.0.1:{ports.get_free_port()}"
        if USE_BINARY_EXECUTABLE:
            run = "tari_indexer"
        else:
            run = " ".join(
                [
                    "cargo",
                    "run",
                    "--bin",
                    "tari_indexer",
                    "--manifest-path",
                    "../tari-dan/Cargo.toml",
                    "--",
                ]
            )
        self.exec = " ".join(
            [
                run,
                "-b",
                f"indexer",
                "--network",
                NETWORK,
                "-p",
                f"indexer.base_node_grpc_address=127.0.0.1:{base_node_grpc_port}",
                "-p",
                "indexer.p2p.transport.type=tcp",
                "-p",
                f"indexer.p2p.transport.tcp.listener_address={self.public_adress}",
                "-p",
                "indexer.p2p.allow_test_addresses=true",
                "-p",
                f"{NETWORK}.p2p.seeds.peer_seeds={','.join(peers)}",
                # "-p",
                # f"indexer.public_address={self.public_adress}",
                "-p",
                f"indexer.p2p.public_addresses={self.public_adress}",
                "-p",
                f"indexer.json_rpc_address={self.json_rpc_address}",
                "-p",
                f"indexer.http_ui_address={self.http_ui_address}",
            ]
        )
        if REDIRECT_INDEXER_STDOUT:
            self.process = subprocess.Popen(self.exec, stdout=open(
                "stdout/indexer.log", "a+"), stderr=subprocess.STDOUT)
        else:
            self.process = subprocess.Popen(self.exec)

        self.jrpc_client = JrpcIndexer(self.json_rpc_address)
        while not os.path.exists(f"indexer/localnet/pid"):
            print("waiting for indexer to start")
            if self.process.poll() is None:
                time.sleep(1)
            else:
                raise Exception(
                    f"Indexer did not start successfully: Exit code:{self.process.poll()}")

    def get_address(self):
        if NETWORK == "localnet":
            indexer_id_file_name = f"./indexer/indexer_id.json"
        else:
            indexer_id_file_name = f"./indexer/indexer_id_{NETWORK}.json"
        while not os.path.exists(indexer_id_file_name):
            time.sleep(0.3)
        f = open(indexer_id_file_name, "rt")
        content = "".join(f.readlines())
        node_id, public_key, public_address = re.search(
            r'"node_id":"(.*?)","public_key":"(.*?)".*"public_address":"(.*?)"', content
        ).groups()
        public_address = public_address.replace("\\/", "/")
        return f"{public_key}::{public_address}"

    def __del__(self):
        print("indexer kill")
        self.process.kill()


class JrpcIndexer:
    def __init__(self, jrpc_url):
        self.url = jrpc_url

    def call(self, method, params=[]):
        response = requests.post(self.url, json={
                                 "jsonrpc": "2.0", "method": method, "id": 1, "params": params})
        print(response.json())
        return response.json()["result"]

    def get_connections(self):
        self.call("get_connections")

    def get_comms_stats(self):
        self.call("get_comms_stats")
